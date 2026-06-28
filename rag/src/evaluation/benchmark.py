"""Dataset generation and retrieval benchmark utilities."""

import json
import logging
import sys
from pydantic import BaseModel
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv
from ranx import Qrels, Run, evaluate

from ..shared.config import (
    BENCHMARK_COMPARISON_CONFIGS,
    BENCHMARK_MIN_CONTEXT_LENGTH,
    BENCHMARK_OUTPUT_DIR,
    BENCHMARK_EVAL_METRICS,
    BENCHMARK_PROMPT,
    CHROMA_COLLECTION_NAME,
    COURSE_PATH,
    EMBEDDING_MODEL,
    KEYWORDS_TO_EXCLUDE,
    OPENROUTER_MODEL_BENCHMARK,
    RERANKER_MODEL,
    RERANKER_TOP_K,
    SUPPORTED_EXTENSIONS,
    TOP_K_RESULTS,
)
from ..ingestion.extractor import extract_elements_from_file, filter_elements, group_elements_by_page
from ..shared.call_model import OpenRouterClient
from ..runtime.retrieval import retrieve
from ..shared.utils import extract_metadata_from_filename

logger = logging.getLogger(__name__)

load_dotenv()

RESULTS_DIR = BENCHMARK_OUTPUT_DIR / "results"


class BenchmarkConfig(BaseModel):
    """Retrieval config for benchmark comparisons."""
    name: str
    embedding_model: str = EMBEDDING_MODEL
    collection_name: str = CHROMA_COLLECTION_NAME
    top_k: int = TOP_K_RESULTS
    reranker_model: str | None = RERANKER_MODEL
    reranker_top_k: int = RERANKER_TOP_K


def create_qa(context: str, page_number: int, filename: str) -> dict | None:
    """Generate one benchmark question for a page."""
    prompt = BENCHMARK_PROMPT.format(page_number=page_number, filename=filename, context=context)
    content = OpenRouterClient().call([{"role": "user", "content": prompt}], model=OPENROUTER_MODEL_BENCHMARK)
    if content is None:
        return None
    try:
        return json.loads(content)
    except (json.JSONDecodeError, TypeError):
        logger.error("Failed to parse OpenRouter response as JSON: %s", content)
        return None


def generate_benchmark_dataset() -> None:
    """Generate BenchmarkQA JSON files from COURSE_PATH documents."""
    docs = [f for ext in SUPPORTED_EXTENSIONS for f in Path(COURSE_PATH).rglob(ext)]

    for file_path in docs:
        file_name = file_path.name
        all_qa = []

        try:
            source_type, course_code, _ = extract_metadata_from_filename(file_name)
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


def build_qrels_and_run(benchmark_file: Path, config: BenchmarkConfig) -> tuple[dict, dict]:
    """
    Build ranx qrels/run dicts from a BenchmarkQA file.

    Returns:
        Pair of qrels/run dictionaries ready for ranx.
    """
    with open(benchmark_file, encoding="utf-8") as f:
        qa_pairs = json.load(f)

    file_stem = benchmark_file.stem.replace("BenchmarkQA-", "")
    _, course_code, _ = extract_metadata_from_filename(file_stem)

    qrels_dict: dict = {}
    run_dict: dict = {}

    for i, qa in enumerate(qa_pairs, start=1):
        question = qa.get("question", "")
        expected_page = str(qa.get("page", "0"))
        expected_file = str(qa.get("filename", ""))
        q_id = f"{file_stem}_q{i}"
        qrels_dict[q_id] = {f"{expected_file}_p{expected_page}": 1}

        results = retrieve(
            course_code,
            question,
            embedding_model=config.embedding_model,
            collection_name=config.collection_name,
            top_k=config.top_k,
            reranker_model=config.reranker_model,
            reranker_top_k=config.reranker_top_k,
        )

        run_dict[q_id] = {}
        for metadata, score in zip(results.metadatas, results.scores):
            pages_str = metadata.get("pages", "[]")
            pages = json.loads(pages_str) if isinstance(pages_str, str) else pages_str
            filename = metadata.get("filename", "Unknown")
            if not pages:
                continue
            # A chunk can match through any page it covers.
            for p in pages:
                page_key = f"{filename}_p{str(p)}"
                run_dict[q_id][page_key] = max(float(score), run_dict[q_id].get(page_key, float("-inf")))

    return qrels_dict, run_dict


def evaluate_benchmark_retrieval_metrics(qrels_dict: dict, run_dict: dict) -> dict:
    """Compute and log retrieval metrics."""
    qrels = Qrels(qrels_dict)
    run = Run(run_dict)
    metrics = evaluate(qrels, run, BENCHMARK_EVAL_METRICS)

    logger.info("Retrieval metrics:")
    for metric, value in metrics.items():
        logger.info("  %s: %.4f", metric, value)

    return metrics


def save_results(data: dict, prefix: str) -> Path:
    """Save benchmark results to a timestamped JSON file."""
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_file = RESULTS_DIR / f"{prefix}_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    logger.info("Results saved to %s", output_file)
    return output_file


def execute_retrieval_benchmark(benchmark_file: Path) -> None:
    """Evaluate one BenchmarkQA JSON with the default config."""
    file_stem = benchmark_file.stem.replace("BenchmarkQA-", "")
    _, course_code, _ = extract_metadata_from_filename(file_stem)
    logger.info("Evaluating: %s | Course: %s", benchmark_file.name, course_code)

    default_config = BenchmarkConfig(name="default")
    qrels_dict, run_dict = build_qrels_and_run(benchmark_file, default_config)
    evaluate_benchmark_retrieval_metrics(qrels_dict, run_dict)


def run_comparison_benchmark(benchmark_files: list[Path]) -> None:
    """Evaluate configured retrieval variants across benchmark files."""
    configs = [BenchmarkConfig(**c) for c in BENCHMARK_COMPARISON_CONFIGS]
    results_list: list[dict] = []

    for config in configs:
        logger.info(
    "=== Running config: %s | embedding_model: %s | reranker_model: %s ===",
    config.name, config.embedding_model, config.reranker_model,
)

        for benchmark_file in benchmark_files:
            try:
                qrels, run = build_qrels_and_run(benchmark_file, config)
                file_metrics = evaluate_benchmark_retrieval_metrics(qrels, run)

                results_list.append({
                    "file": benchmark_file.name.replace("BenchmarkQA-", "").replace(".json", ""),
                    "embedding_model": config.embedding_model,
                    "reranker_model": config.reranker_model,
                    "top_k": config.top_k,
                    "reranker_top_k": config.reranker_top_k,
                    "collection_name": config.collection_name,
                    "metrics": file_metrics,
                })
            except Exception as e:
                logger.error(
                    "Error processing '%s' with config '%s': %s",
                    benchmark_file.name, config.name, e,
                )

    if results_list:
        save_results(results_list, prefix="comparison")
    else:
        logger.warning("No valid results to save.")

if __name__ == "__main__":
    from ..shared.logging_config import setup_logging

    setup_logging()

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
        else:
            execute_retrieval_benchmark(Path(arg))
    else:
        json_files = list(Path(BENCHMARK_OUTPUT_DIR).rglob("BenchmarkQA-*.json"))
        for json_file in json_files:
            execute_retrieval_benchmark(json_file)
