"""
Tutor Benchmark Module.

Evaluates the quality of the Socratic tutor's generation stage independently
from retrieval. Given a student question, does the tutor produce a
pedagogically sound Socratic response?

Unlike the retrieval benchmark (benchmark.py), this module does not measure
whether the right chunks were retrieved — it measures the quality of the
response itself using LLM-as-judge (GPT-4o via IAEdu).

Two main workflows:
    - Dataset generation (--generate): for each document page, calls the IAEdu
      API to produce 2 questions — one regular student question and one
      adversarial question designed to pressure the tutor into bypassing the
      Socratic method.
    - Evaluation (--evaluate): runs the full tutor pipeline (ask()) for each
      question, scores each response with LLM-as-judge on defined criterias, and saves a
      visual report (PNG) to data/benchmark/results/.

Output:
    data/benchmark/BenchmarkTutor-{filename}.json           — dataset files
    data/benchmark/results/benchmark_tutor_{timestamp}.png  — visual report
"""

import json
import logging
import re
import string
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import regex
from dotenv import load_dotenv
from nltk.stem import PorterStemmer

from ..shared.config import (
    BENCHMARK_MIN_CONTEXT_LENGTH,
    BENCHMARK_OUTPUT_DIR,
    COURSE_PATH,
    KEYWORDS_TO_EXCLUDE,
    SUPPORTED_EXTENSIONS,
    TUTOR_BENCHMARK_CRITERIA,
    TUTOR_BENCHMARK_GENERATION_PROMPT,
    TUTOR_BENCHMARK_JUDGE_PROMPT,
)
from ..ingestion.extractor import extract_elements_from_file, filter_elements, group_elements_by_page
from ..shared.iaedu import call_iaedu
from ..shared.models import TutorBenchmarkEntry, TutorEvaluationResult
from ..runtime.retrieval import ask
from ..shared.utils import extract_metadata_from_filename

logger = logging.getLogger(__name__)

load_dotenv()

ps = PorterStemmer()

def normalize_answer(s: str) -> str:
    """Normalize answer for comparison."""
    s = s.replace(',', '')

    def remove_articles(text):
        return regex.sub(r'\b(o|a|os|as|um|uma|uns|umas|de|do|da|dos|das|no|na|nos|nas|ao|aos|à|às|e|em)\b', ' ', text)

    def white_space_fix(text):
        return ' '.join(text.split())

    def remove_punc(text):
        exclude = set(string.punctuation)
        return ''.join(ch for ch in text if ch not in exclude)

    def lower(text):
        return text.lower()

    return white_space_fix(remove_articles(remove_punc(lower(s))))


def f1_score(prediction: str, ground_truth: str) -> float:
    """Compute F1 score with stemming and token matching."""
    prediction_tokens = [ps.stem(w) for w in normalize_answer(prediction).split()]
    ground_truth_tokens = [ps.stem(w) for w in normalize_answer(ground_truth).split()]
    common = Counter(prediction_tokens) & Counter(ground_truth_tokens)
    num_same = sum(common.values())

    if num_same == 0:
        return 0.0

    precision = 1.0 * num_same / len(prediction_tokens) if prediction_tokens else 0.0
    recall = 1.0 * num_same / len(ground_truth_tokens) if ground_truth_tokens else 0.0

    if precision + recall == 0:
        return 0.0

    f1 = (2 * precision * recall) / (precision + recall)
    return f1


def f1_multi_answer(prediction: str, ground_truth: str) -> float:
    """Compute F1 for multi-answer (split by comma)."""
    predictions = [p.strip() for p in prediction.split(',')]
    ground_truths = [g.strip() for g in ground_truth.split(',')]

    return float(np.mean([
        max([f1_score(pred, gt) for pred in predictions])
        for gt in ground_truths
    ]))


def parse_json(content: str) -> any:
    """Parses JSON from a string, stripping markdown code blocks if present."""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", content.strip(), flags=re.MULTILINE)
    return json.loads(cleaned)

def create_questions(context: str, page_number: int, filename: str) -> list[dict] | None:
    """
    Calls the IAEdu API to generate 2 questions from the given page context:
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

    content = call_iaedu(prompt)

    if content is None:
        return None
    try:
        questions = parse_json(content)
        for q in questions:
            q["context"] = context
        return questions
    except (json.JSONDecodeError, TypeError):
        logger.error("Failed to parse IAEdu response as JSON: %s", content)
        return None


def generate_tutor_benchmark_dataset() -> None:
    """
    Generates BenchmarkTutor JSON files from all course documents in COURSE_PATH.

    For each document page with sufficient context, calls create_questions() to
    produce 2 questions (regular + adversarial). Output files are saved to
    BENCHMARK_OUTPUT_DIR as 'BenchmarkTutor-{filename}.json'.
    """
    docs = [f for ext in SUPPORTED_EXTENSIONS for f in Path(COURSE_PATH).rglob(ext)]

    for file_path in docs:
        file_name = file_path.name
        all_questions: list[dict] = []

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

            questions = create_questions(context, page_number, file_name)

            if questions:
                all_questions.extend(questions)

        if all_questions:
            BENCHMARK_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            output_file = BENCHMARK_OUTPUT_DIR / f"BenchmarkTutor-{file_path.name}.json"

            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(all_questions, f, ensure_ascii=False, indent=2)

            logger.info("Saved %d questions to %s", len(all_questions), output_file.name)


def judge_response(entry: TutorBenchmarkEntry, actual_response: str) -> dict | None:
    """
    Calls the IAEdu API (GPT-4o) to score an actual tutor response against
    the four Socratic quality criteria.

    Args:
        entry:           The benchmark entry with context and question.
        actual_response: The response actually generated by the tutor pipeline.

    Returns:
        A dict with integer scores for each criterion, or None on failure.
    """
    prompt = TUTOR_BENCHMARK_JUDGE_PROMPT.format(
        question_type=entry.question_type,
        context=entry.context,
        question=entry.question,
        actual_response=actual_response,
    )

    content = call_iaedu(prompt)

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
    question, then scores each response with the LLM-as-judge.

    Args:
        benchmark_file: Path to a BenchmarkTutor-*.json file.

    Returns:
        A list of TutorEvaluationResult, one per evaluated entry.
    """
    with open(benchmark_file, encoding="utf-8") as f:
        raw_entries = json.load(f)

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

        # Fallback responses score 0 on all criteria — the pipeline found nothing.
        if tutor_response.is_fallback:
            results.append(TutorEvaluationResult(
                filename=entry.filename,
                page=entry.page,
                question=entry.question,
                question_type=entry.question_type,
                actual_response=tutor_response.answer,
                faithfulness=0,
                non_directiveness=0,
                scaffolding=0,
                clarity=0,
                guardrail_robustness=0,
                f1_score=0.0,
                is_fallback=True,
            ))
            continue

        scores = judge_response(entry, tutor_response.answer)

        if scores is None:
            logger.warning("Judge returned no scores for question: %s", entry.question[:60])
            continue

        computed_f1 = (
            f1_multi_answer(tutor_response.answer, entry.expected_answer)
            if entry.expected_answer
            else 0.0
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
            guardrail_robustness=int(scores.get("guardrail_robustness", 0)),
            f1_score=computed_f1,
            is_fallback=False,
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

    non_fallback = [r for r in results if not r.is_fallback]

    if not non_fallback:
        logger.warning("No non-fallback results to plot.")
        return None

    labels = ["Faithfulness", "Non-\ndirectiveness", "Scaffolding", "Clarity", "Guardrail\nRobustness"]

    scores_by_criterion = [
        [getattr(r, c) for r in non_fallback] for c in TUTOR_BENCHMARK_CRITERIA
    ]

    means = [np.mean(s) for s in scores_by_criterion]
    stds = [np.std(s) for s in scores_by_criterion]
    overall_scores = [
        np.mean([getattr(r, c) for c in TUTOR_BENCHMARK_CRITERIA]) for r in non_fallback
    ]

    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Tutor Benchmark — Avaliação da Qualidade da Resposta Socrática", fontsize=13)

    # 1 — Bar chart: mean std per LLM-judge criterion
    ax = axes[0]
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

    # 2 — Histogram: distribution of overall mean LLM-judge score
    ax = axes[1]
    ax.hist(overall_scores, bins=10, range=(0, 5), color="#55A868", alpha=0.85, edgecolor="white")
    ax.set_xlabel("Score médio global")
    ax.set_ylabel("Nº de respostas")
    ax.set_title("LLM-judge: Distribuição do score médio global")
    ax.axvline(
        x=np.mean(overall_scores), color="red", linestyle="--", linewidth=1.2,
        label=f"Média: {np.mean(overall_scores):.2f}",
    )
    ax.legend(fontsize=8)

    # 3 — Bar chart: mean std F1 score by question type
    ax = axes[2]
    qtypes = ["regular", "adversarial"]
    f1_means = []
    f1_stds = []
    for qtype in qtypes:
        subset_f1 = [r.f1_score for r in non_fallback if r.question_type == qtype]
        f1_means.append(np.mean(subset_f1) if subset_f1 else 0.0)
        f1_stds.append(np.std(subset_f1) if subset_f1 else 0.0)
    colors_f1 = ["#4C72B0", "#C44E52"]
    bars_f1 = ax.bar(qtypes, f1_means, yerr=f1_stds, capsize=5, color=colors_f1, alpha=0.85)
    ax.set_ylim(0, 1.1)
    ax.set_ylabel("F1 Score médio (0-1)")
    ax.set_title("F1: Alinhamento com resposta esperada")
    for bar, mean in zip(bars_f1, f1_means):
        ax.text(
            bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.02,
            f"{mean:.3f}", ha="center", fontsize=9,
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
