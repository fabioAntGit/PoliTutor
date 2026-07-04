"""Tutor-response benchmark utilities."""

import json
import logging
import math
import random
import sys
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv

from ..shared.config import (
    BENCHMARK_MIN_CONTEXT_LENGTH,
    BENCHMARK_OUTPUT_DIR,
    EMBEDDING_MODEL,
    OPENROUTER_MODEL_BENCHMARK,
    TUTOR_BENCHMARK_CRITERIA,
    TUTOR_BENCHMARK_GENERATION_PROMPT,
    TUTOR_BENCHMARK_JUDGE_PROMPT,
    TUTOR_BENCHMARK_MAX_QUESTIONS,
)
from ..shared.call_model import OpenRouterClient
from ..shared.chroma_vector_store import get_collection
from ..shared.embedding import get_embedder
from ..shared.models import BenchmarkQuestionSet, JudgeScores, TutorBenchmarkEntry, TutorEvaluationResult
from ..runtime.engine import RagEngine
from ..shared.utils import extract_metadata_from_filename

logger = logging.getLogger(__name__)

load_dotenv()


def compute_semantic_similarity(text_a: str, text_b: str, embedder) -> float:
    """Compute cosine similarity between two texts."""
    vec_a = np.array(embedder.embed_query(text_a))
    vec_b = np.array(embedder.embed_query(text_b))
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(vec_a, vec_b) / (norm_a * norm_b))


def create_questions(context: str, page_number: int, filename: str) -> list[dict] | None:
    """Generate regular and adversarial questions for a page."""
    prompt = TUTOR_BENCHMARK_GENERATION_PROMPT.format(
        page_number=page_number,
        filename=filename,
        context=context,
    )

    result = OpenRouterClient().call_structured(
        [{"role": "user", "content": prompt}],
        schema=BenchmarkQuestionSet,
        max_tokens=800,
        temperature=0.7,
        model=OPENROUTER_MODEL_BENCHMARK,
    )

    if result is None:
        return None
    return [dict(q.model_dump(), context=context) for q in result.questions]


def sample_chunks_from_db(max_questions: int = TUTOR_BENCHMARK_MAX_QUESTIONS) -> list[dict]:
    """
    Sample ChromaDB page contexts for tutor benchmark questions.

    Returns:
        Page dicts with filename, page, context, and source_type.
    """
    collection = get_collection()

    source_types = ["slides", "apontamentos"]
    pages_per_type = (max_questions // 2) // len(source_types)

    sampled: list[dict] = []
    random.seed(42)

    for source_type in source_types:
        # ChromaDB Cloud caps each request at 300.
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

        # Rebuild page context from chunks.
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

        # Keep one document from dominating the sample.
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
    """Generate the tutor benchmark dataset."""
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


def judge_response(entry: TutorBenchmarkEntry, actual_response: str) -> JudgeScores | None:
    """Score a tutor response with the LLM judge."""
    prompt = TUTOR_BENCHMARK_JUDGE_PROMPT.format(
        context=entry.context,
        question=entry.question,
        actual_response=actual_response,
    )

    return OpenRouterClient().call_structured(
        [{"role": "user", "content": prompt}],
        schema=JudgeScores,
        max_tokens=300,
        temperature=0.1,
        model=OPENROUTER_MODEL_BENCHMARK,
    )


def evaluate_tutor_benchmark(benchmark_file: Path) -> list[TutorEvaluationResult]:
    """
    Evaluate tutor responses from a BenchmarkTutor JSON file.

    Returns:
        Results for entries that could be scored or classified.
    """
    with open(benchmark_file, encoding="utf-8") as f:
        raw_entries = json.load(f)

    # Reuse the embedder across all entries.
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

        tutor_response = RagEngine().ask(course_code, entry.question)

        # Input guardrail: judge criteria do not apply.
        if tutor_response.is_guardrail:
            results.append(TutorEvaluationResult(
                filename=entry.filename,
                page=entry.page,
                question=entry.question,
                question_type=entry.question_type,
                actual_response=tutor_response.answer,
                expected_answer="",
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

        # Retrieval fallback.
        if tutor_response.is_fallback:
            results.append(TutorEvaluationResult(
                filename=entry.filename,
                page=entry.page,
                question=entry.question,
                question_type=entry.question_type,
                actual_response=tutor_response.answer,
                expected_answer="",
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

        # Output guardrail fallback.
        if tutor_response.is_output_guardrail:
            results.append(TutorEvaluationResult(
                filename=entry.filename,
                page=entry.page,
                question=entry.question,
                question_type=entry.question_type,
                actual_response=tutor_response.answer,
                expected_answer="",
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
            expected_answer=entry.expected_answer,
            faithfulness=scores.faithfulness,
            non_directiveness=scores.non_directiveness,
            scaffolding=scores.scaffolding,
            clarity=scores.clarity,
            semantic_similarity=sim,
            is_fallback=False,
            is_guardrail=False,
            is_output_guardrail=False,
        ))

    return results


def save_results_json(results: list[TutorEvaluationResult], results_dir: Path, timestamp: str) -> Path:
    """Save normal tutor results sorted by semantic similarity."""
    normal = [
        r for r in results
        if not r.is_fallback and not r.is_guardrail and not r.is_output_guardrail
        and r.semantic_similarity is not None
    ]

    sorted_results = sorted(normal, key=lambda r: r.semantic_similarity, reverse=True)

    export = [
        {
            "rank": i + 1,
            "semantic_similarity": round(r.semantic_similarity, 4),
            "question_type": r.question_type,
            "filename": r.filename,
            "page": r.page,
            "question": r.question,
            "actual_response": r.actual_response,
            "expected_answer": r.expected_answer,
        }
        for i, r in enumerate(sorted_results)
    ]

    output_file = results_dir / f"benchmark_tutor_similarity_{timestamp}.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(export, f, ensure_ascii=False, indent=2)

    logger.info(
        "Similarity results saved to %s (%d entries, highest=%.3f, lowest=%.3f)",
        output_file.name,
        len(export),
        export[0]["semantic_similarity"] if export else 0.0,
        export[-1]["semantic_similarity"] if export else 0.0,
    )
    return output_file


def compute_guardrail_classification_metrics(
    results: list[TutorEvaluationResult],
) -> dict[str, float | int]:
    """Compute binary metrics for the input guardrail."""
    tp = fn = fp = tn = 0

    for r in results:
        is_blocked = r.is_guardrail
        is_adversarial = r.question_type == "adversarial"

        if is_adversarial and is_blocked:
            tp += 1
        elif is_adversarial and not is_blocked:
            fn += 1
        elif not is_adversarial and is_blocked:
            fp += 1
        else:
            tn += 1

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    fpr = fp / (fp + tn) if (fp + tn) > 0 else 0.0

    metrics = {
        "tp": tp,
        "fn": fn,
        "fp": fp,
        "tn": tn,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "fpr": fpr,
    }

    logger.info(
        "Guardrail classification: TP=%d FN=%d FP=%d TN=%d | "
        "Precision=%.3f Recall/TPR=%.3f F1=%.3f FPR=%.3f",
        tp, fn, fp, tn, precision, recall, f1, fpr,
    )

    return metrics


def save_visual_report(results: list[TutorEvaluationResult]) -> Path | None:
    """Save the tutor benchmark visual report."""
    results_dir = BENCHMARK_OUTPUT_DIR / "results"

    # Result buckets.
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

    fig, axes = plt.subplots(3, 2, figsize=(14, 15))
    fig.suptitle("Tutor Benchmark — Avaliação da Qualidade da Resposta Socrática", fontsize=13)

    # Judge scores.
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

    # Overall score.
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

    # Semantic similarity.
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

    # Guardrails.
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

    # Input guardrail metrics.
    ax = axes[2, 0]
    guardrail_metrics = compute_guardrail_classification_metrics(results)

    table_data = [
        ["Métrica", "Valor"],
        ["True Positives (TP)", str(guardrail_metrics["tp"])],
        ["False Negatives (FN)", str(guardrail_metrics["fn"])],
        ["False Positives (FP)", str(guardrail_metrics["fp"])],
        ["True Negatives (TN)", str(guardrail_metrics["tn"])],
        ["", ""],
        ["Precision", f"{guardrail_metrics['precision']:.3f}"],
        ["Recall / TPR", f"{guardrail_metrics['recall']:.3f}"],
        ["F1-Score", f"{guardrail_metrics['f1']:.3f}"],
        ["False Positive Rate", f"{guardrail_metrics['fpr']:.3f}"],
    ]

    ax.axis("off")
    ax.set_title("Input Guardrail — Métricas de Classificação", fontsize=11)

    table = ax.table(
        cellText=table_data[1:],
        colLabels=table_data[0],
        cellLoc="center",
        loc="center",
        colWidths=[0.45, 0.25],
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.4)

    for col_idx in range(2):
        table[0, col_idx].set_facecolor("#4C72B0")
        table[0, col_idx].set_text_props(color="white", fontweight="bold")

    for row_idx in range(1, 5):
        table[row_idx, 0].set_facecolor("#E8EDF3")
        table[row_idx, 1].set_facecolor("#E8EDF3")

    table[5, 0].set_facecolor("white")
    table[5, 1].set_facecolor("white")
    table[5, 0].set_edgecolor("white")
    table[5, 1].set_edgecolor("white")

    table[8, 0].set_text_props(fontweight="bold")
    table[8, 1].set_text_props(fontweight="bold")

    ax.annotate(
        "Classificador: input guardrail (regex) | Positivo: adversarial | Negativo: regular",
        xy=(0.5, 0.02), xycoords="axes fraction", ha="center", fontsize=8, color="gray",
    )

    axes[2, 1].axis("off")

    plt.tight_layout()

    results_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_file = results_dir / f"benchmark_tutor_{timestamp}.png"
    plt.savefig(output_file, dpi=150)
    plt.close()
    logger.info("Visual report saved to %s", output_file)

    save_results_json(results, results_dir, timestamp)

    return output_file

if __name__ == "__main__":
    from ..shared.logging_config import setup_logging

    setup_logging()

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
