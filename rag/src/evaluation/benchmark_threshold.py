"""
Threshold Benchmark Module.

Determines the optimal ChromaDB distance threshold using the elbow method.

Workflow:
    1. Collect all distances returned by ChromaDB across every benchmark question.
    2. Sweep N threshold values across the observed distance range.
    3. For each threshold: filter chunks, rerank, compute IR metrics + fallback rate.
    4. Suggest T* via two criteria: second-derivative elbow and penalised composite score.
    5. Save full results to data/benchmark/results/threshold_sweep_<timestamp>.json.

Usage:
    python -m rag.src.evaluation.benchmark_threshold
    python -m rag.src.evaluation.benchmark_threshold --thresholds 30
"""

import json
import logging
import sys
from datetime import datetime
from pathlib import Path

import numpy as np
from ranx import Qrels, Run, evaluate

from ..shared.config import (
    BENCHMARK_OUTPUT_DIR,
    BENCHMARK_EVAL_METRICS,
    CHROMA_COLLECTION_NAME,
    EMBEDDING_MODEL,
    RERANKER_MODEL,
    RERANKER_TOP_K,
    TOP_K_RESULTS,
)
from ..runtime.retrieval import retrieve_with_config
from ..shared.utils import extract_metadata_from_filename

logger = logging.getLogger(__name__)

RESULTS_DIR = BENCHMARK_OUTPUT_DIR / "results"


def _collect_distances(
    benchmark_files: list[Path],
    embedding_model: str,
    collection_name: str,
    top_k: int,
) -> tuple[list[float], list[float]]:
    """
    Runs retrieval without reranking or threshold filtering for every question
    and separates hit distances from miss distances.

    A "hit" distance is the distance of the chunk that covers the expected page.
    All other distances are "misses".

    Returns:
        (hit_distances, miss_distances) — flat lists of raw ChromaDB cosine distances.
    """
    hit_distances: list[float] = []
    miss_distances: list[float] = []

    for benchmark_file in benchmark_files:
        with open(benchmark_file, encoding="utf-8") as f:
            qa_pairs = json.load(f)

        file_stem = benchmark_file.stem.replace("BenchmarkQA-", "")
        try:
            _, course_code, _ = extract_metadata_from_filename(file_stem)
        except ValueError:
            logger.warning("Skipping %s — cannot extract course code.", benchmark_file.name)
            continue

        for qa in qa_pairs:
            question = qa.get("question", "")
            expected_page = str(qa.get("page", "0"))
            expected_file = str(qa.get("filename", ""))

            results = retrieve_with_config(
                course_code,
                question,
                embedding_model=embedding_model,
                collection_name=collection_name,
                top_k=top_k,
                reranker_model=None,      
                distance_threshold=None,  
            )

            for meta, dist in zip(results.metadatas, results.distances):
                pages_raw = meta.get("pages", "[]")
                pages = json.loads(pages_raw) if isinstance(pages_raw, str) else pages_raw
                filename = meta.get("filename", "")
                is_hit = (filename == expected_file) and (expected_page in [str(p) for p in pages])
                if is_hit:
                    hit_distances.append(dist)
                else:
                    miss_distances.append(dist)

    return hit_distances, miss_distances


def _evaluate_threshold(
    benchmark_files: list[Path],
    threshold: float,
    embedding_model: str,
    collection_name: str,
    top_k: int,
    reranker_model: str | None,
    reranker_top_k: int,
) -> dict:
    """
    Runs the full retrieve+rerank pipeline with a fixed distance threshold and
    returns IR metrics and fallback rate for that threshold value.
    """
    qrels_dict: dict = {}
    run_dict: dict = {}
    n_fallbacks = 0
    n_total = 0

    for benchmark_file in benchmark_files:
        with open(benchmark_file, encoding="utf-8") as f:
            qa_pairs = json.load(f)

        file_stem = benchmark_file.stem.replace("BenchmarkQA-", "")
        try:
            _, course_code, _ = extract_metadata_from_filename(file_stem)
        except ValueError:
            continue

        for i, qa in enumerate(qa_pairs, start=1):
            question = qa.get("question", "")
            expected_page = str(qa.get("page", "0"))
            expected_file = str(qa.get("filename", ""))
            q_id = f"{file_stem}_q{i}"

            qrels_dict[q_id] = {f"{expected_file}_p{expected_page}": 1}
            n_total += 1

            results = retrieve_with_config(
                course_code,
                question,
                embedding_model=embedding_model,
                collection_name=collection_name,
                top_k=top_k,
                reranker_model=reranker_model,
                reranker_top_k=reranker_top_k,
                distance_threshold=threshold,
            )

            if results.is_empty():
                n_fallbacks += 1
                run_dict[q_id] = {}
                continue

            run_dict[q_id] = {}
            for meta, score in zip(results.metadatas, results.scores):
                pages_raw = meta.get("pages", "[]")
                pages = json.loads(pages_raw) if isinstance(pages_raw, str) else pages_raw
                filename = meta.get("filename", "Unknown")
                for p in pages:
                    page_key = f"{filename}_p{str(p)}"
                    run_dict[q_id][page_key] = max(
                        float(score), run_dict[q_id].get(page_key, float("-inf"))
                    )

    qrels = Qrels(qrels_dict)
    run = Run(run_dict)
    metrics = evaluate(qrels, run, BENCHMARK_EVAL_METRICS)

    fallback_rate = n_fallbacks / n_total if n_total > 0 else 0.0
    return {
        "threshold": threshold,
        "fallback_rate": fallback_rate,
        "n_fallbacks": n_fallbacks,
        "n_total": n_total,
        **{k: float(v) for k, v in metrics.items()},
    }


def _suggest_threshold(rows: list[dict], alpha: float = 0.5) -> dict:
    """
    Applies two criteria to suggest the optimal threshold T*:

    1. Second-derivative elbow on hit_rate@5: the threshold just before the
       curve starts flattening (largest positive second derivative).
    2. Penalised composite score: argmax(hit_rate@5 - alpha * fallback_rate).

    Returns a dict with both suggestions and their metrics.
    """
    thresholds = np.array([r["threshold"] for r in rows])
    hit_rates = np.array([r.get("hit_rate@5", 0.0) for r in rows])
    fallback_rates = np.array([r["fallback_rate"] for r in rows])

    if len(hit_rates) >= 3:
        second_deriv = np.gradient(np.gradient(hit_rates, thresholds), thresholds)
        elbow_idx = int(np.argmax(second_deriv))
    else:
        elbow_idx = int(np.argmax(hit_rates))

    composite = hit_rates - alpha * fallback_rates
    composite_idx = int(np.argmax(composite))

    return {
        "elbow": {
            "threshold": float(thresholds[elbow_idx]),
            "hit_rate@5": float(hit_rates[elbow_idx]),
            "fallback_rate": float(fallback_rates[elbow_idx]),
        },
        "composite": {
            "threshold": float(thresholds[composite_idx]),
            "hit_rate@5": float(hit_rates[composite_idx]),
            "fallback_rate": float(fallback_rates[composite_idx]),
            "alpha": alpha,
        },
    }


def run_threshold_sweep(
    benchmark_files: list[Path],
    n_thresholds: int = 20,
    embedding_model: str = EMBEDDING_MODEL,
    collection_name: str = CHROMA_COLLECTION_NAME,
    top_k: int = TOP_K_RESULTS,
    reranker_model: str | None = RERANKER_MODEL,
    reranker_top_k: int = RERANKER_TOP_K,
    composite_alpha: float = 0.5,
) -> Path:
    """
    Full threshold sweep: collect distances, define grid, evaluate each threshold,
    apply elbow method, and save results.

    Args:
        benchmark_files:  List of BenchmarkQA-*.json files.
        n_thresholds:     Number of threshold values to test.
        embedding_model:  Embedding model identifier.
        collection_name:  ChromaDB collection name.
        top_k:            Number of candidates retrieved from ChromaDB.
        reranker_model:   Reranker model identifier, or None to skip reranking.
        reranker_top_k:   Number of results kept after reranking.
        composite_alpha:  Weight of fallback_rate penalty in composite criterion.

    Returns:
        Path to the saved JSON results file.
    """
    logger.info("=== Phase 1: Collecting distance distribution ===")
    hit_dists, miss_dists = _collect_distances(
        benchmark_files, embedding_model, collection_name, top_k
    )
    all_dists = hit_dists + miss_dists

    if not all_dists:
        logger.error("No distances collected — are there BenchmarkQA files and a populated ChromaDB?")
        sys.exit(1)

    d_min = float(np.min(all_dists))
    d_max = float(np.max(all_dists))
    logger.info(
        "Distance range: [%.4f, %.4f] | hits=%d, misses=%d",
        d_min, d_max, len(hit_dists), len(miss_dists),
    )
    logger.info(
        "Hit distance percentiles  [10, 25, 50, 75, 90]: %s",
        np.percentile(hit_dists, [10, 25, 50, 75, 90]).round(4).tolist() if hit_dists else "N/A",
    )
    logger.info(
        "Miss distance percentiles [10, 25, 50, 75, 90]: %s",
        np.percentile(miss_dists, [10, 25, 50, 75, 90]).round(4).tolist() if miss_dists else "N/A",
    )

    thresholds = np.linspace(d_min, d_max, num=n_thresholds).tolist()

    logger.info("=== Phase 2: Sweeping %d threshold values ===", n_thresholds)
    rows: list[dict] = []
    for t in thresholds:
        logger.info("  Evaluating threshold=%.4f ...", t)
        row = _evaluate_threshold(
            benchmark_files, t,
            embedding_model, collection_name,
            top_k, reranker_model, reranker_top_k,
        )
        rows.append(row)
        logger.info(
            "    hit_rate@5=%.4f  ndcg@5=%.4f  fallback_rate=%.4f  fallbacks=%d/%d",
            row.get("hit_rate@5", 0), row.get("ndcg@5", 0),
            row["fallback_rate"], row["n_fallbacks"], row["n_total"],
        )

    logger.info("=== Phase 3: Elbow detection ===")
    suggestions = _suggest_threshold(rows, alpha=composite_alpha)
    logger.info("Elbow suggestion:     T=%.4f  hit_rate@5=%.4f  fallback_rate=%.4f",
        suggestions["elbow"]["threshold"],
        suggestions["elbow"]["hit_rate@5"],
        suggestions["elbow"]["fallback_rate"],
    )
    logger.info("Composite suggestion: T=%.4f  hit_rate@5=%.4f  fallback_rate=%.4f  (alpha=%.2f)",
        suggestions["composite"]["threshold"],
        suggestions["composite"]["hit_rate@5"],
        suggestions["composite"]["fallback_rate"],
        composite_alpha,
    )

    output = {
        "config": {
            "embedding_model": embedding_model,
            "collection_name": collection_name,
            "top_k": top_k,
            "reranker_model": reranker_model,
            "reranker_top_k": reranker_top_k,
            "n_thresholds": n_thresholds,
            "composite_alpha": composite_alpha,
        },
        "distance_stats": {
            "d_min": d_min,
            "d_max": d_max,
            "n_hits": len(hit_dists),
            "n_misses": len(miss_dists),
            "hit_percentiles": {
                str(p): float(np.percentile(hit_dists, p))
                for p in [10, 25, 50, 75, 90]
            } if hit_dists else {},
            "miss_percentiles": {
                str(p): float(np.percentile(miss_dists, p))
                for p in [10, 25, 50, 75, 90]
            } if miss_dists else {},
        },
        "suggestions": suggestions,
        "sweep": rows,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_path = RESULTS_DIR / f"threshold_sweep_{timestamp}.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    logger.info("Results saved to %s", output_path)
    return output_path


if __name__ == "__main__":
    from ..shared.logging_config import setup_logging

    setup_logging()

    import argparse

    parser = argparse.ArgumentParser(description="Threshold sweep benchmark for retrieval distance calibration.")
    parser.add_argument("--thresholds", type=int, default=20, help="Number of threshold values to test (default: 20)")
    parser.add_argument("--benchmark-dir", type=Path, default=BENCHMARK_OUTPUT_DIR,
                        help="Directory containing BenchmarkQA-*.json files (default: BENCHMARK_OUTPUT_DIR from config)")
    args = parser.parse_args()

    benchmark_dir: Path = args.benchmark_dir
    json_files = list(benchmark_dir.rglob("BenchmarkQA-*.json"))
    if not json_files:
        logger.error("No BenchmarkQA-*.json files found in %s", benchmark_dir)
        sys.exit(1)

    logger.info("Found %d benchmark file(s) in %s.", len(json_files), benchmark_dir)
    run_threshold_sweep(json_files, n_thresholds=args.thresholds)
