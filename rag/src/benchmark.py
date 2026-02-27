import json
import os
import sys
import uuid
import requests
import logging

from pathlib import Path
from dotenv import load_dotenv
from ranx import Qrels, Run, evaluate
from config import BENCHMARK_OUTPUT_DIR, BENCHMARK_PROMPT, COURSE_PATH, KEYWORDS_TO_EXCLUDE, BENCHMARK_MIN_CONTEXT_LENGTH, BENCHMARK_EVAL_METRICS, SUPPORTED_EXTENSIONS
from pdf_extractor import extract_elements_from_file, filter_elements, group_elements_by_page
from utils import extract_metadata_from_filename
from retrieval import retrieve

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger(__name__)

load_dotenv()

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

def execute_retrieval_benchmark(benchmark_file: Path):
    """Reads a BenchmarkQA JSON and shows ChromaDB retrieval results for each question."""
    with open(benchmark_file, encoding="utf-8") as f:
        qa_pairs = json.load(f)

    file_stem = benchmark_file.stem.replace("BenchmarkQA-", "")
    _, course_code = extract_metadata_from_filename(file_stem)

    logger.info("Evaluating: %s | Course: %s", benchmark_file.name, course_code)

    qrels_dict = {}
    run_dict = {}

    for i, qa in enumerate(qa_pairs, start=1):
        question = qa.get("question", "")
        expected_page = str(qa.get("page", "0"))
        expected_file = str(qa.get("filename", ""))
        q_id = f"{file_stem}_q{i}"
        qrels_dict[q_id] = {f"{expected_file}_p{expected_page}": 1}

        results = retrieve(course_code, question)

        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]

        if "scores" in results and len(results["scores"]) > 0:
            scores = results["scores"][0]
        else:
            scores = [1.0 / (d + 1e-5) for d in distances]
    
        run_dict[q_id] = {}

        for doc_id, distance, metadata, document, score in zip(ids, distances, metadatas, documents, scores):
            pages_str = metadata.get('pages', '[]')
            pages = json.loads(pages_str) if isinstance(pages_str, str) else pages_str

            filename = metadata.get('filename', 'Unknown')

            for p in pages:
                page_key = f"{filename}_p{str(p)}"
                
                current_score = run_dict[q_id].get(page_key, float('-inf'))
                run_dict[q_id][page_key] = max(score, current_score)

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
        logger.info("  %s: %.4f", metric, value)

    return metrics
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--generate":
            generate_benchmark_dataset()
        else:
            execute_retrieval_benchmark(Path(arg))
    else:
        json_files = list(Path(BENCHMARK_OUTPUT_DIR).rglob("BenchmarkQA-*.json"))
        for json_file in json_files:
            execute_retrieval_benchmark(json_file)