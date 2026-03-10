import json
import os
import sys
import uuid
import requests
import logging
from dataclasses import dataclass

from pathlib import Path
from dotenv import load_dotenv
from ranx import Qrels, Run, evaluate
from config import (
    BENCHMARK_OUTPUT_DIR, BENCHMARK_PROMPT, COURSE_PATH, KEYWORDS_TO_EXCLUDE,
    BENCHMARK_MIN_CONTEXT_LENGTH, BENCHMARK_EVAL_METRICS, SUPPORTED_EXTENSIONS,
    EMBEDDING_MODEL, CHROMA_COLLECTION_NAME, TOP_K_RESULTS, RERANKER_MODEL,
    RERANKER_TOP_K, BENCHMARK_COMPARISON_CONFIGS, BENCHMARK_THRESHOLD_SWEEP,
)
from extractor import extract_elements_from_file, filter_elements, group_elements_by_page
from utils import extract_metadata_from_filename
from retrieval import retrieve, retrieve_with_config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()


@dataclass
class BenchmarkConfig:
    """Defines a retrieval configuration to evaluate in the comparison benchmark."""
    name: str
    embedding_model: str = EMBEDDING_MODEL
    collection_name: str = CHROMA_COLLECTION_NAME
    top_k: int = TOP_K_RESULTS
    reranker_model: str | None = RERANKER_MODEL
    reranker_top_k: int = RERANKER_TOP_K
    score_threshold: float | None = None


def create_qa(context: str, page_number: int, filename: str) -> dict:
    """
    Sends a page context to the LLM endpoint and returns a generated Q&A pair.
    """
    prompt = BENCHMARK_PROMPT.format(page_number=page_number, filename=filename, context=context)

    thread_id = uuid.uuid4().hex[:20]

    url = os.getenv("IAEDU_API_ENDPOINT")
    
    files = {
        "channel_id": (None, os.getenv("IAEDU_API_CHANNEL")),
        "thread_id": (None, thread_id),
        "user_info": (None, "{}"),
        "message": (None, prompt),
    }
    
    headers = {
        "x-api-key": os.getenv("IAEDU_API_KEY"),
    }
    
    response = requests.post(url, files=files, headers=headers)

    if not response.ok:
        logger.error(f"IAEdu API error {response.status_code}: {response.text}")
    
    for line in response.iter_lines():
        if line:
            decoded = line.decode("utf-8")
            try:
                data = json.loads(decoded)
                if data.get("type") == "message":
                    content = data["content"]["content"]
                    return json.loads(content)
            except json.JSONDecodeError:
                continue
    
    return None

def generate_benchmark_dataset():
    """
    Generates BenchmarkQA JSON files from all files found in COURSE_PATH.
    """
    docs = [f for ext in SUPPORTED_EXTENSIONS for f in Path(COURSE_PATH).rglob(ext)]
    all_qa = []

    for file_path in docs:
        file_name = file_path.name

        try:
            source_type, course_code = extract_metadata_from_filename(file_name)
        except ValueError:
            continue

        elements = extract_elements_from_file(str(file_path))
        filtered_elements = filter_elements(elements, KEYWORDS_TO_EXCLUDE)
        grouped_pages = group_elements_by_page(
            filtered_elements,
            source_filename=file_name,
            source_type=source_type,
            course_code=course_code,
            skip_pages=1,
        )

        for page in grouped_pages:
            page_number = page["metadata"]["page_number"]
            context = page["text"].strip()

            if len(context) < BENCHMARK_MIN_CONTEXT_LENGTH:
                continue

            qa = create_qa(context, page_number, file_name)
            if qa:
                all_qa.append(qa)

        if all_qa:
            BENCHMARK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = BENCHMARK_OUTPUT_DIR / f"BenchmarkQA-{file_path.name}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_qa, f, ensure_ascii=False, indent=2)
            logger.info("Saved %d Q&A pairs to %s", len(all_qa), output_file.name)
            all_qa = []

def _build_qrels_and_run(benchmark_file: Path, config: BenchmarkConfig) -> tuple[dict, dict]:
    """
    Reads a BenchmarkQA file and runs retrieval for each question using `config`.
    Returns (qrels_dict, run_dict) ready for ranx evaluation.
    """
    with open(benchmark_file, encoding="utf-8") as f:
        qa_pairs = json.load(f)

    file_stem = benchmark_file.stem.replace("BenchmarkQA-", "")
    _, course_code = extract_metadata_from_filename(file_stem)

    qrels_dict: dict = {}
    run_dict: dict = {}

    for i, qa in enumerate(qa_pairs, start=1):
        question     = qa.get("question", "")
        expected_page = str(qa.get("page", "0"))
        expected_file = str(qa.get("filename", ""))
        q_id = f"{file_stem}_q{i}"
        qrels_dict[q_id] = {f"{expected_file}_p{expected_page}": 1}

        results = retrieve_with_config(
            course_code,
            question,
            embedding_model=config.embedding_model,
            collection_name=config.collection_name,
            top_k=config.top_k,
            reranker_model=config.reranker_model,
            reranker_top_k=config.reranker_top_k,
            score_threshold=config.score_threshold,
        )

        ids       = results.get("ids",       [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
        scores    = results.get("scores",    [[]])[0]

        run_dict[q_id] = {}
        for _, distance, metadata, _, score in zip(ids, distances, metadatas, documents, scores):
            pages_str = metadata.get("pages", "[]")
            pages = json.loads(pages_str) if isinstance(pages_str, str) else pages_str
            filename = metadata.get("filename", "Unknown")
            if not pages:
                continue
            # A chunk may span multiple pages. Register the score for every covered
            # page so that the evaluator can match any of them against qrels.
            for p in pages:
                page_key = f"{filename}_p{str(p)}"
                run_dict[q_id][page_key] = max(float(score), run_dict[q_id].get(page_key, float("-inf")))

    return qrels_dict, run_dict


def execute_retrieval_benchmark(benchmark_file: Path) -> None:
    """Reads a BenchmarkQA JSON and evaluates ChromaDB retrieval using the default config."""
    file_stem = benchmark_file.stem.replace("BenchmarkQA-", "")
    _, course_code = extract_metadata_from_filename(file_stem)
    logger.info("Evaluating: %s | Course: %s", benchmark_file.name, course_code)

    default_config = BenchmarkConfig(name="default")
    qrels_dict, run_dict = _build_qrels_and_run(benchmark_file, default_config)
    evaluate_benchmark_retrieval_metrics(qrels_dict, run_dict)

def evaluate_benchmark_retrieval_metrics(qrels_dict: dict, run_dict: dict) -> dict:
    """
    Computes and prints retrieval metrics using ranx.
    """
    qrels = Qrels(qrels_dict)
    run = Run(run_dict)

    metrics = evaluate(qrels, run, BENCHMARK_EVAL_METRICS)

    logger.info("Retrieval metrics:")
    for metric, value in metrics.items():
        logger.info(f"  {metric}: {value:.4f}")

    return metrics
    
def _print_comparison_table(results: dict[str, dict]) -> None:
    """Prints a formatted side-by-side comparison table of metrics across configs."""
    if not results:
        logger.warning("No comparison results to display.")
        return

    metrics   = list(next(iter(results.values())).keys())
    col_width = max(len(name) for name in results) + 2
    m_width   = 14

    header    = f"{'Config':<{col_width}}" + "".join(f"{m:>{m_width}}" for m in metrics)
    separator = "-" * len(header)

    print("\n" + separator)
    print(header)
    print(separator)
    for config_name, config_metrics in results.items():
        row = f"{config_name:<{col_width}}" + "".join(
            f"{config_metrics.get(m, 0.0):>{m_width}.4f}" for m in metrics
        )
        print(row)
    print(separator + "\n")


def sweep_threshold_benchmark(benchmark_files: list[Path]) -> None:
    """
    Finds the optimal score threshold for the configured reranker.

    Runs retrieval ONCE (no threshold) and applies each threshold value in
    memory — no extra database or embedding calls per threshold step.
    At the end prints a comparison table and highlights the best threshold.
    """
    reranker_model = BENCHMARK_THRESHOLD_SWEEP["reranker_model"]
    start          = BENCHMARK_THRESHOLD_SWEEP["start"]
    stop           = BENCHMARK_THRESHOLD_SWEEP["stop"]
    step           = BENCHMARK_THRESHOLD_SWEEP["step"]
    primary_metric = BENCHMARK_THRESHOLD_SWEEP["primary_metric"]

    logger.info(
        "Threshold sweep: collecting raw scores with reranker '%s'...", reranker_model
    )

    # Step 1 — retrieve once, no threshold
    config = BenchmarkConfig(name="sweep", reranker_model=reranker_model, score_threshold=None)
    combined_qrels: dict = {}
    combined_run_raw: dict = {}

    for benchmark_file in benchmark_files:
        try:
            qrels, run = _build_qrels_and_run(benchmark_file, config)
            combined_qrels.update(qrels)
            combined_run_raw.update(run)
        except Exception as e:
            logger.error("Error processing '%s': %s", benchmark_file.name, e)

    if not combined_qrels or not combined_run_raw:
        logger.error("No data collected — aborting sweep.")
        return

    total_queries = len(combined_qrels)

    # Step 2 — generate threshold values
    n_steps    = round((stop - start) / step)
    thresholds = [round(start + i * step, 6) for i in range(n_steps + 1)]

    # Step 3 — apply each threshold in memory and compute metrics
    sweep_results: dict[str, dict] = {}
    qrels_obj = Qrels(combined_qrels)

    for threshold in thresholds:
        filtered_run: dict = {}
        covered = 0
        for q_id, page_scores in combined_run_raw.items():
            kept = {k: v for k, v in page_scores.items() if v >= threshold}
            if kept:
                filtered_run[q_id] = kept
                covered += 1

        label = f"t={threshold:+.2f} ({covered}/{total_queries})"

        if not filtered_run:
            sweep_results[label] = {m: 0.0 for m in BENCHMARK_EVAL_METRICS}
            continue

        metrics = dict(evaluate(qrels_obj, Run(filtered_run), BENCHMARK_EVAL_METRICS, make_comparable=True))
        sweep_results[label] = metrics

    _print_comparison_table(sweep_results)

    # Step 4 — report best threshold
    best_label = max(sweep_results, key=lambda k: sweep_results[k].get(primary_metric, 0.0))
    best_value = sweep_results[best_label][primary_metric]
    best_threshold = float(best_label.split("=")[1].split()[0])
    logger.info(
        "Best threshold for '%s': %.2f  →  %s = %.4f",
        primary_metric, best_threshold, primary_metric, best_value,
    )


def run_comparison_benchmark(benchmark_files: list[Path]) -> None:
    """
    Runs all configurations defined in BENCHMARK_COMPARISON_CONFIGS against
    the provided benchmark files and prints a side-by-side metrics table.

    Each config is evaluated over all files combined so that the final metrics
    reflect the full dataset, not individual files.
    """
    configs = [BenchmarkConfig(**c) for c in BENCHMARK_COMPARISON_CONFIGS]
    all_results: dict[str, dict] = {}

    for config in configs:
        logger.info("=== Running config: %s ===", config.name)
        combined_qrels: dict = {}
        combined_run:   dict = {}

        for benchmark_file in benchmark_files:
            try:
                qrels, run = _build_qrels_and_run(benchmark_file, config)
                combined_qrels.update(qrels)
                combined_run.update(run)
            except Exception as e:
                logger.error(
                    "Error processing '%s' with config '%s': %s",
                    benchmark_file.name, config.name, e,
                )

        if combined_qrels and combined_run:
            metrics = evaluate_benchmark_retrieval_metrics(combined_qrels, combined_run)
            all_results[config.name] = metrics
        else:
            logger.warning("No valid data for config '%s'. Skipping.", config.name)

    _print_comparison_table(all_results)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--generate":
            generate_benchmark_dataset()
        elif arg == "--compare":
            json_files = list(Path(BENCHMARK_OUTPUT_DIR).rglob("BenchmarkQA-*.json"))
            if not json_files:
                logger.warning("No BenchmarkQA-*.json files found in %s", BENCHMARK_OUTPUT_DIR)
            else:
                run_comparison_benchmark(json_files)
        elif arg == "--sweep-threshold":
            json_files = list(Path(BENCHMARK_OUTPUT_DIR).rglob("BenchmarkQA-*.json"))
            if not json_files:
                logger.warning("No BenchmarkQA-*.json files found in %s", BENCHMARK_OUTPUT_DIR)
            else:
                sweep_threshold_benchmark(json_files)
        else:
            execute_retrieval_benchmark(Path(arg))
    else:
        json_files = list(Path(BENCHMARK_OUTPUT_DIR).rglob("BenchmarkQA-*.json"))
        for json_file in json_files:
            execute_retrieval_benchmark(json_file)