"""
Plot threshold sweep results from benchmark_threshold.py output.

Usage:
    python -m src.evaluation.plot_threshold_sweep <path_to_json>
"""

import json
import sys
from pathlib import Path

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

RECOMMENDED_T = 0.9301327684210527  # first threshold with fallback ≈ 0 and hit@5 plateaus


def plot(json_path: Path) -> None:
    with open(json_path, encoding="utf-8") as f:
        data = json.load(f)

    sweep = data["sweep"]

    thresholds = np.array([r["threshold"] for r in sweep])
    hit_rate   = np.array([r["hit_rate@5"] for r in sweep])
    ndcg       = np.array([r["ndcg@5"] for r in sweep])
    mrr        = np.array([r["mrr@5"] for r in sweep])
    fallback   = np.array([r["fallback_rate"] for r in sweep])

    rec_idx = int(np.argmin(np.abs(thresholds - RECOMMENDED_T)))
    rec_t   = thresholds[rec_idx]
    rec_hit = hit_rate[rec_idx]
    rec_fb  = fallback[rec_idx]
    rec_ndcg = ndcg[rec_idx]

    plt.style.use("seaborn-v0_8-whitegrid")
    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(10, 7), sharex=True,
        gridspec_kw={"height_ratios": [2, 1], "hspace": 0.08},
    )

    # ── Plateau shading ───────────────────────────────────────────────
    for ax in (ax1, ax2):
        ax.axvspan(rec_t, thresholds[-1], color="mediumseagreen", alpha=0.08, zorder=0)

    # ── Top: IR metrics ───────────────────────────────────────────────
    ax1.plot(thresholds, hit_rate * 100, "o-",  color="#1f77b4", lw=2,   ms=5, label="Hit Rate@5", zorder=3)
    ax1.plot(thresholds, ndcg     * 100, "s--", color="#ff7f0e", lw=1.8, ms=4, label="NDCG@5",     zorder=3)
    ax1.plot(thresholds, mrr      * 100, "^:",  color="#2ca02c", lw=1.8, ms=4, label="MRR@5",      zorder=3)

    ax1.axvline(rec_t, color="#d62728", lw=2, ls="-", zorder=4, label=f"Threshold recomendado  T = {rec_t:.4f}")

    # Annotation box
    ax1.annotate(
        f"T = {rec_t:.4f}\nHit@5 = {rec_hit:.1%}\nNDCG@5 = {rec_ndcg:.1%}\nFallback = {rec_fb:.1%}",
        xy=(rec_t, rec_hit * 100),
        xytext=(rec_t + 0.07, 55),
        fontsize=9.5,
        color="#d62728",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#d62728", lw=1.2),
        arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.2),
        zorder=5,
    )

    ax1.set_ylabel("Score (%)", fontsize=11)
    ax1.set_ylim(-3, 105)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%g%%"))
    ax1.legend(loc="lower right", fontsize=9.5, framealpha=0.9)
    ax1.set_title(
        "Análise do Threshold de Distância — Pipeline de Recuperação (bge-m3 + gte-reranker-modernbert)",
        fontsize=11, fontweight="bold", pad=10,
    )

    # ── Bottom: Fallback rate ─────────────────────────────────────────
    ax2.plot(thresholds, fallback * 100, "D-", color="#d62728", lw=2, ms=5, label="Taxa de Fallback", zorder=3)
    ax2.fill_between(thresholds, fallback * 100, alpha=0.18, color="#d62728", zorder=2)
    ax2.axvline(rec_t, color="#d62728", lw=2, ls="-", zorder=4)

    ax2.set_ylabel("Fallback (%)", fontsize=11)
    ax2.set_xlabel("Threshold de distância (ChromaDB cosine)", fontsize=11)
    ax2.set_ylim(-3, 108)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%g%%"))
    ax2.legend(loc="upper right", fontsize=9.5, framealpha=0.9)

    # Plateau label
    plateau_patch = mpatches.Patch(color="mediumseagreen", alpha=0.25, label="Zona estável (fallback = 0%)")
    ax2.legend(handles=[
        plt.Line2D([0], [0], color="#d62728", lw=2, marker="D", ms=5, label="Taxa de Fallback"),
        plateau_patch,
    ], loc="upper right", fontsize=9.5, framealpha=0.9)

    # X ticks at every evaluated threshold
    ax2.set_xticks(thresholds)
    ax2.set_xticklabels([f"{t:.3f}" for t in thresholds], rotation=45, ha="right", fontsize=7.5)

    plt.tight_layout()
    out_path = json_path.with_suffix(".png")
    plt.savefig(out_path, dpi=200, bbox_inches="tight")
    print(f"Gráfico guardado em: {out_path}")
    plt.show()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.evaluation.plot_threshold_sweep <path_to_json>")
        sys.exit(1)
    plot(Path(sys.argv[1]))
