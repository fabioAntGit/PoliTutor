"""
Tutor Benchmark Module.

Evaluates the quality of the Socratic tutor's generation stage independently
from retrieval. Given a student question, does the tutor produce a
pedagogically sound Socratic response?

Unlike the retrieval benchmark (benchmark.py), this module does not measure
whether the right chunks were retrieved — it measures the quality of the
response itself using LLM-as-judge (GPT-4o via OpenRouter).

Two main workflows:
    - Dataset generation (--generate): samples up to TUTOR_BENCHMARK_MAX_QUESTIONS
      pages from ChromaDB (stratified across slides / apontamentos and documents),
      then calls OpenRouter to produce 2 questions per page — one regular student
      question and one adversarial question designed to pressure the tutor into
      bypassing the Socratic method.

    - Evaluation (--evaluate): runs the full tutor pipeline (ask()) for each
      question, scores each response with LLM-as-judge on defined criteria, F1 score and
      saves a visual report (PNG) to data/benchmark/results/.

Output:
    data/benchmark/BenchmarkTutor-sample.json              — generated dataset
    data/benchmark/results/benchmark_tutor_{timestamp}.png — visual report
"""

import json
import logging
import math
import random
import re
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

from config import (
    BENCHMARK_MIN_CONTEXT_LENGTH,
    BENCHMARK_OUTPUT_DIR,
    EMBEDDING_MODEL,
    OPENROUTER_MODEL_BENCHMARK,
    TUTOR_BENCHMARK_CRITERIA,
    TUTOR_BENCHMARK_GENERATION_PROMPT,
    TUTOR_BENCHMARK_JUDGE_PROMPT,
    TUTOR_BENCHMARK_MAX_QUESTIONS,
)
from call_model import call_openrouter
from database import get_collection
from embedding import get_embedder
from models import TutorBenchmarkEntry, TutorEvaluationResult
from retrieval import ask
from utils import extract_metadata_from_filename

logger = logging.getLogger(__name__)

load_dotenv()


def compute_semantic_similarity(text_a: str, text_b: str, embedder) -> float:
    """
    Computes cosine similarity between two texts using the project's embedding model (bge-m3).

    Captures semantic equivalence between the actual tutor response and the expected
    Socratic answer, independently of lexical variation. A score of 1.0 means identical
    direction in embedding space; 0.0 means orthogonal (unrelated).

    Args:
        text_a:   First text (actual tutor response).
        text_b:   Second text (expected Socratic answer).
        embedder: Initialised embedder instance (reused across calls for efficiency).

    Returns:
        Cosine similarity in [0, 1].
    """
    vec_a = np.array(embedder.embed_query(text_a))
    vec_b = np.array(embedder.embed_query(text_b))
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def parse_json(content: str) -> any:
    """Parses JSON from a string, stripping markdown code blocks if present."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)

def create_questions(context: str, page_number: int, filename: str) -> list[dict] | None:
    """
    Calls OpenRouter to generate 2 questions from the given page context:
    one regular student question and one adversarial question designed to
    pressure the tutor into bypassing the Socratic method.

    Args:
        context:     Page text to use as generation context.
        page_number: Page number within the source document.
        filename:    Source document filename.

    Returns:
        A list of 2 dicts, each with keys 'filename', 'page', 'question',
        'question_type', 'expected_answer', and 'context'. Returns None on failure.
    """
    prompt = TUTOR_BENCHMARK_GENERATION_PROMPT.format(
        page_number=page_number,
        filename=filename,
        context=context,
    )

    content = call_openrouter(prompt, max_tokens=800, temperature=0.7, model=OPENROUTER_MODEL_BENCHMARK)

    if content is None:
        return None
    try:
        questions = parse_json(content)
        for q in questions:
            q["context"] = context
        return questions
    except (json.JSONDecodeError, TypeError):
        logger.error("Failed to parse OpenRouter response as JSON: %s", content)
        return None


def sample_chunks_from_db(max_questions: int = TUTOR_BENCHMARK_MAX_QUESTIONS) -> list[dict]:
    """
    Fetches text chunks from ChromaDB and returns a stratified sample of
    page-level context units ready for question generation.

    Runs one query per source type (slides / apontamentos) with limit=300
    (ChromaDB Cloud per-request cap), groups chunks by (filename, primary_page)
    to reconstruct page context, then samples equally from each type with a
    per-document cap so no single document dominates.

    Args:
        max_questions: Total target number of questions (2 per sampled page).

    Returns:
        List of dicts with keys: filename, page, context, source_type.
    """
    collection = get_collection()

    source_types = ["slides", "apontamentos"]
    pages_per_type = (max_questions // 2) // len(source_types)

    sampled: list[dict] = []
    random.seed(42)

    for source_type in source_types:
        # Paginate within the 300-per-request quota until all chunks are fetched
        documents: list[str] = []
        metadatas: list[dict] = []
        offset = 0
        batch_size = 300

        while True:
            result = collection.get(
                include=["documents", "metadatas"],
                where={"$and": [{"type": "text"}, {"source": source_type}]},
                limit=batch_size,
                offset=offset,
            )
            batch_docs = result.get("documents", []) or []
            batch_metas = result.get("metadatas", []) or []
            if not batch_docs:
                break
            documents.extend(batch_docs)
            metadatas.extend(batch_metas)
            offset += len(batch_docs)
            if len(batch_docs) < batch_size:
                break

        # Group chunks by (filename, primary_page) to reconstruct page context
        page_groups: dict[tuple[str, int], dict] = {}
        for doc, meta in zip(documents, metadatas):
            filename = meta.get("filename", "")
            pages_raw = meta.get("pages", "[]")
            try:
                pages = json.loads(pages_raw) if isinstance(pages_raw, str) else pages_raw
                primary_page = pages[0] if pages else 0
            except (json.JSONDecodeError, IndexError):
                primary_page = 0

            key = (filename, primary_page)
            if key not in page_groups:
                page_groups[key] = {
                    "filename": filename,
                    "page": primary_page,
                    "texts": [],
                }
            page_groups[key]["texts"].append(doc)

        # Build valid page units (concatenated context above min-length)
        valid_pages: list[dict] = []
        dropped = 0
        for group in page_groups.values():
            context = "\n\n".join(group["texts"])
            if len(context) < BENCHMARK_MIN_CONTEXT_LENGTH:
                dropped += 1
                continue
            valid_pages.append({
                "filename": group["filename"],
                "page": group["page"],
                "context": context,
                "source_type": source_type,
            })

        # Cap per document to avoid one doc dominating
        by_doc: dict[str, list[dict]] = {}
        for page in valid_pages:
            by_doc.setdefault(page["filename"], []).append(page)

        num_docs = max(1, len(by_doc))
        cap_per_doc = max(2, math.ceil(pages_per_type / num_docs))

        type_sample: list[dict] = []
        for doc_pages in by_doc.values():
            random.shuffle(doc_pages)
            type_sample.extend(doc_pages[:cap_per_doc])

        random.shuffle(type_sample)
        taken = type_sample[:pages_per_type]
        sampled.extend(taken)

        logger.info(
            "source=%s | chunks=%d | page_groups=%d | valid=%d (dropped=%d) | docs=%d | sampled=%d",
            source_type,
            len(documents),
            len(page_groups),
            len(valid_pages),
            dropped,
            len(by_doc),
            len(taken),
        )

    logger.info(
        "Total sampled %d pages → %d questions | target=%d",
        len(sampled),
        len(sampled) * 2,
        max_questions,
    )
    return sampled


def generate_tutor_benchmark_dataset() -> None:
    """
    Generates a single BenchmarkTutor-sample.json from a stratified sample of
    ChromaDB text chunks.

    ChromaDB query, ensuring questions are generated from the same text units
    the retriever uses. Skips generation if the output file already exists.
    """
    output_file = BENCHMARK_OUTPUT_DIR / "BenchmarkTutor-sample.json"

    if output_file.exists():
        logger.warning(
            "Output file already exists: %s — delete it manually to regenerate.",
            output_file.name,
        )
        return

    pages = sample_chunks_from_db()

    if not pages:
        logger.error("No pages sampled from ChromaDB. Is the collection populated?")
        return

    all_questions: list[dict] = []
    for page in pages:
        questions = create_questions(page["context"], page["page"], page["filename"])
        if questions:
            all_questions.extend(questions)

    if not all_questions:
        logger.error("No questions generated. Check OpenRouter API connectivity.")
        return

    BENCHMARK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(all_questions, f, ensure_ascii=False, indent=2)

    logger.info("Saved %d questions to %s", len(all_questions), output_file.name)


def judge_response(entry: TutorBenchmarkEntry, actual_response: str) -> dict | None:
    """
    Calls OpenRouter to score an actual tutor response against
    the five Socratic quality criteria.

    Args:
        entry:           The benchmark entry with context and question.
        actual_response: The response actually generated by the tutor pipeline.

    Returns:
        A dict with integer scores for each criterion, or None on failure.
    """
    prompt = TUTOR_BENCHMARK_JUDGE_PROMPT.format(
        context=entry.context,
        question=entry.question,
        actual_response=actual_response,
    )

    content = call_openrouter(prompt, max_tokens=300, temperature=0.1, model=OPENROUTER_MODEL_BENCHMARK)

    if content is None:
        return None
    try:
        return parse_json(content)
    except (json.JSONDecodeError, TypeError):
        logger.error("Failed to parse judge response as JSON: %s", content)
        return None


def evaluate_tutor_benchmark(benchmark_file: Path) -> list[TutorEvaluationResult]:
    """
    Reads a BenchmarkTutor JSON file, runs the full tutor pipeline for each
    question, then scores each response with the LLM-as-judge and semantic similarity.

    Args:
        benchmark_file: Path to a BenchmarkTutor-*.json file.

    Returns:
        A list of TutorEvaluationResult, one per evaluated entry.
    """
    with open(benchmark_file, encoding="utf-8") as f:
        raw_entries = json.load(f)

    # Initialise embedder once — reused across all entries for efficiency.
    embedder = get_embedder(EMBEDDING_MODEL)

    results: list[TutorEvaluationResult] = []

    for raw in raw_entries:
        entry = TutorBenchmarkEntry(
            filename=raw.get("filename", ""),
            page=str(raw.get("page", "")),
            context=raw.get("context", ""),
            question=raw.get("question", ""),
            question_type=raw.get("question_type", "regular"),
            expected_answer=raw.get("expected_answer", ""),
        )

        try:
            _, course_code, _ = extract_metadata_from_filename(entry.filename)
        except ValueError:
            logger.warning("Skipping entry with invalid filename: %s", entry.filename)
            continue

        logger.info(
            "Evaluating [%s]: %s | page %s",
            entry.question_type, entry.filename, entry.page,
        )

        tutor_response = ask(course_code, entry.question)

        # Input guardrail blocked the query before reaching the LLM — criteria not applicable.
        if tutor_response.is_guardrail:
            results.append(TutorEvaluationResult(
                filename=entry.filename,
                page=entry.page,
                question=entry.question,
                question_type=entry.question_type,
                actual_response=tutor_response.answer,
                faithfulness=None,
                non_directiveness=None,
                scaffolding=None,
                clarity=None,
                semantic_similarity=None,
                is_fallback=False,
                is_guardrail=True,
                is_output_guardrail=False,
            ))
            continue

        # Retriever found no relevant chunks — generation was never called.
        if tutor_response.is_fallback:
            results.append(TutorEvaluationResult(
                filename=entry.filename,
                page=entry.page,
                question=entry.question,
                question_type=entry.question_type,
                actual_response=tutor_response.answer,
                faithfulness=None,
                non_directiveness=None,
                scaffolding=None,
                clarity=None,
                semantic_similarity=None,
                is_fallback=True,
                is_guardrail=False,
                is_output_guardrail=False,
            ))
            continue

        # Output guardrail triggered — LLM produced a direct answer, replaced with Socratic redirect.
        if tutor_response.is_output_guardrail:
            results.append(TutorEvaluationResult(
                filename=entry.filename,
                page=entry.page,
                question=entry.question,
                question_type=entry.question_type,
                actual_response=tutor_response.answer,
                faithfulness=None,
                non_directiveness=None,
                scaffolding=None,
                clarity=None,
                semantic_similarity=None,
                is_fallback=False,
                is_guardrail=False,
                is_output_guardrail=True,
            ))
            continue

        scores = judge_response(entry, tutor_response.answer)

        if scores is None:
            logger.warning("Judge returned no scores for question: %s", entry.question[:60])
            continue

        sim = (
            compute_semantic_similarity(tutor_response.answer, entry.expected_answer, embedder)
            if entry.expected_answer
            else None
        )

        results.append(TutorEvaluationResult(
            filename=entry.filename,
            page=entry.page,
            question=entry.question,
            question_type=entry.question_type,
            actual_response=tutor_response.answer,
            faithfulness=int(scores.get("faithfulness", 0)),
            non_directiveness=int(scores.get("non_directiveness", 0)),
            scaffolding=int(scores.get("scaffolding", 0)),
            clarity=int(scores.get("clarity", 0)),
            semantic_similarity=sim,
            is_fallback=False,
            is_guardrail=False,
            is_output_guardrail=False,
        ))

    return results


def save_visual_report(results: list[TutorEvaluationResult]) -> Path | None:
    """
    Generates a 1×3 matplotlib figure and saves it as a timestamped PNG.

    Subplots:
        1. Bar chart — mean std per LLM-judge criterion (all non-fallback results).
        2. Histogram — distribution of overall mean LLM-judge score.
        3. Bar chart — mean std F1 score by question type (regular vs adversarial).

    Args:
        results: List of evaluated tutor responses.

    Returns:
        Path to the written PNG file, or None if no plottable results.
    """
    results_dir = BENCHMARK_OUTPUT_DIR / "results"

    # Separate results into four categories
    normal           = [r for r in results if not r.is_fallback and not r.is_guardrail and not r.is_output_guardrail]
    fallback         = [r for r in results if r.is_fallback]
    guardrail_blocked = [r for r in results if r.is_guardrail]
    output_guardrail = [r for r in results if r.is_output_guardrail]
    adversarial_total = [r for r in results if r.question_type == "adversarial"]

    if not normal:
        logger.warning("No normal results to plot.")
        return None

    labels = ["Faithfulness", "Non-\ndirectiveness", "Scaffolding", "Clarity"]

    scores_by_criterion = [
        [getattr(r, c) for r in normal] for c in TUTOR_BENCHMARK_CRITERIA
    ]

    means = [np.mean(s) for s in scores_by_criterion]
    stds = [np.std(s) for s in scores_by_criterion]
    overall_scores = [
        np.mean([getattr(r, c) for c in TUTOR_BENCHMARK_CRITERIA]) for r in normal
    ]

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle("Tutor Benchmark — Avaliação da Qualidade da Resposta Socrática", fontsize=13)

    # 1 — Bar chart: mean ± std per LLM-judge criterion (normal responses only)
    ax = axes[0, 0]
    bars = ax.bar(labels, means, yerr=stds, capsize=5, color="#4C72B0", alpha=0.85)
    ax.set_ylim(0, 5.5)
    ax.set_ylabel("Score médio (1-5)")
    ax.set_title("LLM-judge: Score médio por critério")
    ax.axhline(y=3, color="gray", linestyle="--", linewidth=0.8, label="Score neutro (3)")
    for bar, mean in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
            f"{mean:.2f}", ha="center", fontsize=9,
        )
    ax.legend(fontsize=8)

    # 2 — Histogram: distribution of overall mean LLM-judge score (normal responses only)
    ax = axes[0, 1]
    ax.hist(overall_scores, bins=10, range=(0, 5), color="#55A868", alpha=0.85, edgecolor="white")
    ax.set_xlabel("Score médio global")
    ax.set_ylabel("Nº de respostas")
    ax.set_title("LLM-judge: Distribuição do score médio global")
    ax.axvline(
        x=np.mean(overall_scores), color="red", linestyle="--", linewidth=1.2,
        label=f"Média: {np.mean(overall_scores):.2f}",
    )
    ax.legend(fontsize=8)

    # 3 — Bar chart: mean ± std semantic similarity by question type (normal responses only)
    ax = axes[1, 0]
    qtypes = ["regular", "adversarial"]
    sim_means = []
    sim_stds = []
    for qtype in qtypes:
        subset = [
            r.semantic_similarity for r in normal
            if r.question_type == qtype and r.semantic_similarity is not None
        ]
        sim_means.append(np.mean(subset) if subset else 0.0)
        sim_stds.append(np.std(subset) if subset else 0.0)
    colors_sim = ["#4C72B0", "#C44E52"]
    bars_sim = ax.bar(qtypes, sim_means, yerr=sim_stds, capsize=5, color=colors_sim, alpha=0.85)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("Similaridade semântica média (0-1)")
    ax.set_title("Similaridade semântica com resposta socrática esperada (bge-m3)")
    for bar, mean in zip(bars_sim, sim_means):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
            f"{mean:.3f}", ha="center", fontsize=9,
        )

    # 4 — Defesa em camadas: fallback + input guardrail + output guardrail
    ax = axes[1, 1]
    total = len(results)
    n_adv = len(adversarial_total)

    fallback_rate        = len(fallback) / total * 100 if total else 0
    input_guardrail_rate = len(guardrail_blocked) / n_adv * 100 if n_adv else 0
    output_guardrail_rate = len(output_guardrail) / n_adv * 100 if n_adv else 0

    special_labels = [
        "Fallback\n(sem retrieval)\n% do total",
        "Input guardrail\n(regex bloqueou)\n% das adversariais",
        "Output guardrail\n(LLM falhou, corrigido)\n% das adversariais",
    ]
    special_values = [fallback_rate, input_guardrail_rate, output_guardrail_rate]
    special_colors = ["#DD8452", "#C44E52", "#8B0000"]
    bars_s = ax.bar(special_labels, special_values, color=special_colors, alpha=0.85)
    ax.set_ylim(0, 110)
    ax.set_ylabel("Percentagem (%)")
    ax.set_title("Robustez do sistema — defesa em camadas")
    for bar, val in zip(bars_s, special_values):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
            f"{val:.1f}%", ha="center", fontsize=10, fontweight="bold",
        )
    system_prompt_rate = 100 - input_guardrail_rate - output_guardrail_rate
    ax.annotate(
        f"Total: {total} | Normal: {len(normal)} | Fallback: {len(fallback)} | "
        f"Input guardrail: {len(guardrail_blocked)} | Output guardrail: {len(output_guardrail)}\n"
        f"Adversariais tratadas pelo system prompt sem falha: {system_prompt_rate:.1f}%",
        xy=(0.5, -0.16), xycoords="axes fraction", ha="center", fontsize=8, color="gray",
    )

    plt.tight_layout()

    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_file = results_dir / f"benchmark_tutor_{timestamp}.png"
    plt.savefig(output_file, dpi=150)
    plt.close()
    logger.info("Visual report saved to %s", output_file)
    return output_file

if __name__ == "__main__":
    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "--generate":
            generate_tutor_benchmark_dataset()
        elif arg == "--evaluate":
            if len(sys.argv) > 2:
                benchmark_files = [Path(sys.argv[2])]
            else:
                benchmark_files = list(Path(BENCHMARK_OUTPUT_DIR).rglob("BenchmarkTutor-*.json"))

            if not benchmark_files:
                logger.warning("No BenchmarkTutor-*.json files found in %s", BENCHMARK_OUTPUT_DIR)
                sys.exit(1)

            all_results: list[TutorEvaluationResult] = []
            for bf in benchmark_files:
                logger.info("=== Evaluating: %s ===", bf.name)
                all_results.extend(evaluate_tutor_benchmark(bf))

            if all_results:
                save_visual_report(all_results)
        else:
            logger.error("Unknown argument: %s. Use --generate or --evaluate.", arg)
            sys.exit(1)
    else:
        benchmark_files = list(Path(BENCHMARK_OUTPUT_DIR).rglob("BenchmarkTutor-*.json"))
        if not benchmark_files:
            logger.warning("No BenchmarkTutor-*.json files found. Run --generate first.")
            sys.exit(1)

        all_results = []
        for bf in benchmark_files:
            logger.info("=== Evaluating: %s ===", bf.name)
            all_results.extend(evaluate_tutor_benchmark(bf))

        if all_results:
            save_visual_report(all_results)