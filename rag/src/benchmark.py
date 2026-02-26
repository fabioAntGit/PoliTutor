import json
import os
import sys
import uuid
import requests

from pathlib import Path
from dotenv import load_dotenv
from ranx import Qrels, Run, evaluate
from config import BENCHMARK_OUTPUT_DIR, BENCHMARK_PROMPT, COURSE_PATH, KEYWORDS_TO_EXCLUDE
from embedding import connect_chromadb, get_embedder
from pdf_extractor import extract_elements_from_pdf, filter_elements, group_elements_by_page
from retrieval import query_collection
from utils import extract_metadata_from_filename

load_dotenv()

def create_qa(context: str, page_number: int, filename: str) -> dict:
    """
    Sends a page context to the LLM endpoint and returns a generated Q&A pair.
    """
    prompt = BENCHMARK_PROMPT.format(page_number=page_number, filename=filename, context=context)

    thread_id = uuid.uuid4().hex[:20]

    url = os.getenv("IAEDU_API_ENDPOINT")
    
    files = {
        "channel_id": (None, os.getenv("IAEDU_API_CANAL")),
        "thread_id": (None, thread_id),
        "user_info": (None, "{}"),
        "message": (None, prompt),
    }
    
    headers = {
        "x-api-key": os.getenv("IAEDU_API_KEY"),
    }
    
    response = requests.post(url, files=files, headers=headers)
    response.raise_for_status()
    
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
    Generates BenchmarkQA JSON files from all PDF files found in COURSE_PATH.
    """
    pdf_files = list(Path(COURSE_PATH).rglob("*.pdf"))
    all_qa = []

    for pdf_path in pdf_files:
        file_name = pdf_path.name

        try:
            source_type, course_code = extract_metadata_from_filename(file_name)
        except ValueError:
            continue

        elements = extract_elements_from_pdf(str(pdf_path))
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

            if len(context) < 200:
                continue

            qa = create_qa(context, page_number, file_name)
            if qa:
                all_qa.append(qa)

        if all_qa:
            BENCHMARK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = BENCHMARK_OUTPUT_DIR / f"BenchmarkQA-{pdf_path.stem}.json"
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_qa, f, ensure_ascii=False, indent=2)
            print(f"Saved {len(all_qa)} Q&A pairs -> {output_file.name}")
            all_qa = []

def execute_retrieval_benchmark(benchmark_file: Path):
    """Reads a BenchmarkQA JSON and shows ChromaDB retrieval results for each question."""
    with open(benchmark_file, encoding="utf-8") as f:
        qa_pairs = json.load(f)

    pdf_stem = benchmark_file.stem.replace("BenchmarkQA-", "")
    _, course_code = extract_metadata_from_filename(f"{pdf_stem}.pdf")

    collection = connect_chromadb()
    embedder = get_embedder()

    print(f"\n{'='*60}")
    print(f"Evaluating: {benchmark_file.name} | Course: {course_code}")
    print(f"{'='*60}")

    qrels_dict = {}
    run_dict = {}

    for i, qa in enumerate(qa_pairs, start=1):
        question = qa.get("question", "")
        expected_page = str(qa.get("page", "0"))
        expected_file = str(qa.get("filename", ""))
        q_id = f"q{i}"
        qrels_dict[q_id] = {f"{expected_file}_p{expected_page}": 1}

        results = query_collection(collection, embedder, question, course_code)

        ids = results.get("ids", [[]])[0]
        distances = results.get("distances", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        documents = results.get("documents", [[]])[0]
    
        run_dict[q_id] = {}
        for doc_id, distance, metadata, document in zip(ids, distances, metadatas, documents):
            pages = json.loads(metadata.get('pages', []))
            filename = metadata.get('filename', 'Unknown')
            score = float(1 - distance)
            
            for p in pages:
                page_key = f"{filename}_p{str(p)}"
                run_dict[q_id][page_key] = max(score, run_dict[q_id].get(page_key, 0))

    evaluate_benchmark_retrieval_metrics(qrels_dict, run_dict)

def evaluate_benchmark_retrieval_metrics(qrels_dict: dict, run_dict: dict) -> dict:
    """
    Computes and prints retrieval metrics using ranx.
    """
    qrels = Qrels(qrels_dict)
    run = Run(run_dict)

    metrics = evaluate(qrels, run, ["hit_rate@5", "mrr@5", "ndcg@5", "map@5", "precision@5", "recall@5"])

    print(f"\n{'='*60}")
    for metric, value in metrics.items():
        print(f"{metric}: {value:.4f}")

    return metrics
    
if __name__ == "__main__":
    if len(sys.argv) > 1:
        execute_retrieval_benchmark(Path(sys.argv[1]))
    else:
        json_files = list(Path(BENCHMARK_OUTPUT_DIR).rglob("BenchmarkQA-*.json"))
        for json_file in json_files:
            execute_retrieval_benchmark(json_file)