#!/usr/bin/env python3
"""
Generate column-width paper figures from the committed result JSONs.

The experiment scripts emit wide working figures (5.3--9.1in). For the
two-column USENIX draft, this script regenerates the two figures the paper
keeps at single-column width (3.4in) with fonts sized for that measure. It
reads ONLY the result JSONs — no experiment is re-run and no number can
change. Deterministic: same JSON in, same PDF out (up to matplotlib
version).

Outputs (under paper/figures/):
  fig_frontier_column.pdf   <- experiments/results/m3_frontier.json
  fig_controls_column.pdf   <- experiments/results/perturbation_model_controls.json

Usage: python3 scripts/build_paper_figures.py
"""

import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "experiments" / "results"
OUT = ROOT / "paper" / "figures"
OUT.mkdir(parents=True, exist_ok=True)

plt.rcParams.update({
    "font.size": 8, "axes.titlesize": 8, "axes.labelsize": 8,
    "xtick.labelsize": 7, "ytick.labelsize": 7, "legend.fontsize": 6.5,
    "pdf.fonttype": 42,
})


def load(name):
    with open(RESULTS / name) as fh:
        return json.load(fh)


def fig_frontier():
    m = load("m3_frontier.json")
    pts = m["operating_points"]
    fpr = [p["federated_fpr"] for p in pts]
    rec = [p["federated_recall"] for p in pts]
    labels = [f"({p['b']},{p['r']})" for p in pts]

    fig, ax = plt.subplots(figsize=(3.4, 2.5))
    ax.plot(fpr, rec, "o-", color="#1f4e79", lw=1.2, ms=4)
    for x, y, lbl in zip(fpr, rec, labels):
        ax.annotate(lbl, (x, y), textcoords="offset points",
                    xytext=(6, -2), fontsize=6.5)
    ax.plot([0, 1], [0, 1], ls=":", color="#c00000", lw=0.8,
            label="random (recall = FPR)")
    ax.set_xscale("symlog", linthresh=1e-3)
    ax.set_xlim(-2e-5, 1.15)
    ax.set_ylim(-0.03, 1.03)
    ax.set_xlabel("False positive rate (symlog)")
    ax.set_ylabel("Recall")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, loc="upper left")
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "fig_frontier_column.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  wrote paper/figures/fig_frontier_column.pdf  (from m3_frontier.json)")


MODEL_STYLE = {
    "per_message_mean": ("#7f7f7f", "o", "-", "per-msg mean (baseline)"),
    "per_message_max": ("#b0b0b0", "v", "-", "per-msg max"),
    "per_message_top5": ("#d0a000", "s", "-", "per-msg top-5"),
    "conv_concat": ("#2e7d32", "D", "-", "conv concat (order-inv.)"),
    "conv_mean": ("#c00000", "^", "-", "conv mean (order-inv.)"),
    "sequence": ("#1f4e79", "o", "-", "sequence (pos-weighted)"),
    "sequence_shuffled": ("#7b1fa2", "x", "--", "sequence, shuffled order"),
}


def fig_controls():
    d = load("perturbation_model_controls.json")
    conds = d["conditions"]
    xs = [c["strength"] for c in conds]

    fig, ax = plt.subplots(figsize=(3.4, 2.9))
    for m, (color, marker, ls, lbl) in MODEL_STYLE.items():
        means = [c[m]["auc"]["mean"] for c in conds]
        stds = [c[m]["auc"]["std"] for c in conds]
        ax.errorbar(xs, means, yerr=stds, color=color, marker=marker, ls=ls,
                    lw=1.1, ms=3.5, capsize=2, label=lbl)
    ax.set_xticks(xs)
    ax.set_xlabel("Perturbation strength (discourse noise)")
    ax.set_ylabel("AUC (mean $\\pm$ std, 5 seeds)")
    ax.grid(alpha=0.3)
    ax.legend(frameon=False, ncol=1, loc="lower left")
    fig.tight_layout(pad=0.4)
    fig.savefig(OUT / "fig_controls_column.pdf", bbox_inches="tight")
    plt.close(fig)
    print("  wrote paper/figures/fig_controls_column.pdf  "
          "(from perturbation_model_controls.json)")


def main():
    print("Generating column-width paper figures from result JSONs ...")
    fig_frontier()
    fig_controls()
    print("Done.")


if __name__ == "__main__":
    main()
