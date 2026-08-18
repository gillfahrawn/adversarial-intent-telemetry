#!/usr/bin/env python3
"""
False-positive substrate analysis (D7).

For a Trust & Safety detection scheme, the false-positive rate on
*structurally similar benign* conversations is not optional validation:
mental-health peer support, LGBTQ+ youth conversations, harm-reduction
discussion, and ordinary adolescent relationship talk share surface features
(age discussion, meeting plans, secrecy language, romantic language) with
grooming transcripts. PAN 2012 is the local substrate, so this experiment
uses structurally similar benign PAN negatives as a proxy population.

Design
------
- Author-disjoint split (same as exp_m3_author_split.py / exp_m3_frontier.py).
- Substrate sampling uses keyword/structure filters on *test-split negatives*
  — never classifier predictions, to avoid circularity. A conversation enters
  the substrate pool if any message matches at least one filter category.
- A random benign control set of the same size is sampled from test negatives
  matching no filter.
- Two detectors are evaluated on both sets:
    (a) the MinHash signature protocol at the recommended (b=16, r=16)
        operating point, querying against the federated pool of
        training-positive signatures (the protocol's core primitive);
    (b) the per-message LinearSVC baseline, thresholded at FPR <= 0.05
        calibrated on the full author-disjoint test set.
- Sampling is repeated over multiple seeds; proportions carry Wilson 95% CIs.

If structural_FPR exceeds control_FPR, that is a finding (it motivates the
per-class FP-ceiling / human-review framing), not a failure.

Outputs: experiments/results/fp_substrate.json / .png / .pdf.
No raw PAN message text is printed or written to any output.
"""

import json
import re
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.svm import LinearSVC

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
OUT = SCRIPT_DIR / "results"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(SCRIPT_DIR))
from exp_m3_author_split import (  # noqa: E402
    SEED, L, VOCAB_SIZE, DATA_XML, DATA_PRED,
    make_hash_funcs, conv_to_sig, build_band_index, query_band_index,
    load_predators, parse_pan12, author_disjoint_split,
)
from exp_trajectory_lift import operating_point_at_fpr  # noqa: E402

BAND_B, BAND_R = 16, 16
FPR_TARGET = 0.05
N_TARGET = 500
SAMPLING_SEEDS = [0, 1, 2]

# Structural markers used ONLY to sample benign conversations. These are
# neutral lexical patterns (age talk, meeting plans, secrecy, romance), not
# abuse content. Deliberately over-inclusive: the point is surface similarity.
KEYWORD_FILTERS = {
    "age_discussion": [
        r"\basl\b", r"\ba/s/l\b",
        r"\bhow old (are|r) (you|u)\b",
        r"\b(i'?m|i am|im) 1[0-7]\b",
        r"\b1[0-7] ?(yo|y/o|yrs? old|years old)\b",
    ],
    "meeting_plans": [
        r"\bmeet (up|me|you|u)\b", r"\bcome over\b",
        r"\bpick (you|u) up\b", r"\bmy (address|place|house)\b",
    ],
    "secrecy_isolation": [
        r"\b(our|a) secret\b", r"\bdon'?t tell\b",
        r"\bhome alone\b", r"\bparents (aren'?t|are not|not) (home|here)\b",
    ],
    "romantic_relationship": [
        r"\b(boy|girl)friend\b", r"\blove (you|u)\b",
        r"\bmiss (you|u)\b", r"\bkiss\b", r"\bcute\b",
    ],
}
COMPILED = {cat: [re.compile(p, re.IGNORECASE) for p in pats]
            for cat, pats in KEYWORD_FILTERS.items()}


def match_categories(messages: list) -> set:
    """Return the set of filter categories any message text matches."""
    cats = set()
    for _, text in messages:
        for cat, pats in COMPILED.items():
            if cat in cats:
                continue
            if any(p.search(text) for p in pats):
                cats.add(cat)
        if len(cats) == len(COMPILED):
            break
    return cats


def wilson_ci(k: int, n: int, z: float = 1.96) -> list:
    if n == 0:
        return [0.0, 1.0]
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return [float(max(0.0, center - half)), float(min(1.0, center + half))]


def main() -> None:
    missing = [p for p in (DATA_XML, DATA_PRED) if not p.exists()]
    if missing:
        print("ERROR: Required PAN 2012 data files not found:", file=sys.stderr)
        for p in missing:
            print(f"  {p}", file=sys.stderr)
        print(
            "\nPAN 2012 is public research data distributed by the PAN organizers;"
            "\nit is not redistributed in this repository. See data/pan12/README.md"
            "\nfor citation and how to obtain it, then place the training XML and"
            "\npredator list in data/pan12/train/ and re-run.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("Parsing PAN 2012 XML …")
    predators = load_predators(DATA_PRED)
    conversations = parse_pan12(DATA_XML, predators)
    train, test, *_ = author_disjoint_split(conversations, predators)
    test_neg = [c for c in test if c[1] == 0]
    train_pos = [c for c in train if c[1] == 1]
    print(f"  author-disjoint split: train={len(train)}  test={len(test)} "
          f"(test negatives={len(test_neg)}, train positives={len(train_pos)})")

    # ── Partition test negatives into substrate pool vs control pool ───────────
    print("Applying keyword/structure filters to test negatives …")
    substrate_pool, control_pool = [], []
    category_counts = {cat: 0 for cat in KEYWORD_FILTERS}
    for conv in test_neg:
        cats = match_categories(conv[2])
        if cats:
            substrate_pool.append(conv)
            for cat in cats:
                category_counts[cat] += 1
        else:
            control_pool.append(conv)
    print(f"  substrate pool={len(substrate_pool)}  control pool={len(control_pool)}")
    print(f"  category hits: { {k: v for k, v in category_counts.items()} }")

    n_sample = min(N_TARGET, len(substrate_pool), len(control_pool))
    if n_sample < N_TARGET:
        print(f"  NOTE: pool smaller than target; sampling n={n_sample} per set.")

    # ── Detector (a): MinHash signature protocol at (16,16) ────────────────────
    print("Building MinHash pool index from training positives …")
    a_hf, b_hf, p_hf = make_hash_funcs(L, VOCAB_SIZE)
    pool_sigs = []
    for _, _, msgs in train_pos:
        sig = conv_to_sig(msgs, a_hf, b_hf, p_hf)
        if sig is not None:
            pool_sigs.append(sig)
    pool_index = build_band_index(pool_sigs, BAND_B, BAND_R)
    print(f"  {len(pool_sigs)} valid training-positive signatures in pool")

    sig_hit_cache: dict = {}

    def minhash_hit(conv) -> bool:
        cid = conv[0]
        if cid not in sig_hit_cache:
            sig = conv_to_sig(conv[2], a_hf, b_hf, p_hf)
            sig_hit_cache[cid] = (
                False if sig is None
                else query_band_index(pool_index, sig, BAND_B, BAND_R))
        return sig_hit_cache[cid]

    # ── Detector (b): per-message LinearSVC at clean FPR<=0.05 threshold ───────
    print("Training per-message LinearSVC on author-disjoint training split …")
    train_msg_texts, train_msg_labels = [], []
    for _, label, msgs in train:
        for _, txt in msgs:
            train_msg_texts.append(txt if txt else " ")
            train_msg_labels.append(label)
    vectorizer = TfidfVectorizer(max_features=10_000, analyzer="char_wb",
                                 ngram_range=(3, 5), sublinear_tf=True)
    X_train = vectorizer.fit_transform(train_msg_texts)
    svc = LinearSVC(random_state=SEED)
    svc.fit(X_train, np.array(train_msg_labels, dtype=int))

    def svc_score(conv) -> float:
        texts = [t if t else " " for _, t in conv[2]]
        if not texts:
            return 0.0
        return float(svc.decision_function(vectorizer.transform(texts)).mean())

    print("Calibrating classifier threshold on the full author-disjoint test set …")
    y_test = np.array([label for _, label, _ in test], dtype=int)
    test_scores = np.array([svc_score(c) for c in test])
    thr, _, _, _, actual_fpr = operating_point_at_fpr(y_test, test_scores, FPR_TARGET)
    score_cache = {test[i][0]: float(test_scores[i]) for i in range(len(test))}
    print(f"  threshold={thr:.4f} (overall test FPR={actual_fpr:.4f})")

    # ── Sample, evaluate, repeat over seeds ─────────────────────────────────────
    per_seed = []
    for ss in SAMPLING_SEEDS:
        rng = np.random.default_rng(SEED + 100 * (ss + 1))
        sub_idx = rng.choice(len(substrate_pool), size=n_sample, replace=False)
        ctl_idx = rng.choice(len(control_pool), size=n_sample, replace=False)
        substrate = [substrate_pool[i] for i in sub_idx]
        control = [control_pool[i] for i in ctl_idx]

        row = {"sampling_seed": ss, "n_substrate": n_sample, "n_control": n_sample}
        for det, fn in (("minhash_16_16", minhash_hit),
                        ("classifier_fpr05", lambda c: score_cache[c[0]] >= thr)):
            k_sub = sum(1 for c in substrate if fn(c))
            k_ctl = sum(1 for c in control if fn(c))
            row[det] = {
                "structural_FPR": k_sub / n_sample,
                "structural_FPR_wilson95": wilson_ci(k_sub, n_sample),
                "control_FPR": k_ctl / n_sample,
                "control_FPR_wilson95": wilson_ci(k_ctl, n_sample),
                "n_structural_fp": k_sub,
                "n_control_fp": k_ctl,
            }
        per_seed.append(row)
        print(f"  [seed {ss}] minhash: sub={row['minhash_16_16']['structural_FPR']:.4f} "
              f"ctl={row['minhash_16_16']['control_FPR']:.4f} | "
              f"classifier: sub={row['classifier_fpr05']['structural_FPR']:.4f} "
              f"ctl={row['classifier_fpr05']['control_FPR']:.4f}")

    def pooled(det, key_fp, key_n=None):
        k = sum(r[det][key_fp] for r in per_seed)
        n = n_sample * len(per_seed)
        return k, n

    summary = {}
    for det in ("minhash_16_16", "classifier_fpr05"):
        k_sub, n_tot = pooled(det, "n_structural_fp")
        k_ctl, _ = pooled(det, "n_control_fp")
        summary[det] = {
            "structural_FPR_mean": float(np.mean(
                [r[det]["structural_FPR"] for r in per_seed])),
            "control_FPR_mean": float(np.mean(
                [r[det]["control_FPR"] for r in per_seed])),
            "structural_FPR_pooled_wilson95": wilson_ci(k_sub, n_tot),
            "control_FPR_pooled_wilson95": wilson_ci(k_ctl, n_tot),
            "elevated": bool(np.mean([r[det]["structural_FPR"] for r in per_seed])
                             > np.mean([r[det]["control_FPR"] for r in per_seed])),
            "note": "Samples across seeds overlap (drawn from the same pools), "
                    "so pooled CIs understate independence; per-seed rows are "
                    "the primary evidence.",
        }

    output = {
        "experiment": "fp_substrate",
        "substrate_type": "structurally_similar_benign",
        "dataset": "PAN 2012 SPI training XML, author-disjoint split "
                   "(same as exp_m3_author_split.py); substrate/control drawn "
                   "from test-split negatives only",
        "split_type": "author_disjoint_80_20",
        "split_seed": SEED,
        "sampling_seeds": SAMPLING_SEEDS,
        "n_substrate": n_sample,
        "n_control": n_sample,
        "substrate_pool_size": len(substrate_pool),
        "control_pool_size": len(control_pool),
        "keyword_filter_used": KEYWORD_FILTERS,
        "filter_category_hits_in_pool": category_counts,
        "detectors": {
            "minhash_16_16": "banded MinHash signature match at (b=16, r=16) "
                             "against federated pool of training-positive "
                             "signatures (protocol primitive)",
            "classifier_fpr05": f"per-message LinearSVC, threshold at "
                                f"FPR<={FPR_TARGET} calibrated on full "
                                f"author-disjoint test set "
                                f"(threshold={thr:.4f}, overall "
                                f"test FPR={actual_fpr:.4f})",
        },
        "per_seed": per_seed,
        "summary": summary,
        "interpretation": (
            "If structural_FPR > control_FPR, benign conversations that share "
            "surface features with grooming transcripts absorb a "
            "disproportionate share of false positives. That is a finding "
            "motivating per-class FP ceilings and human review, not a failure "
            "of the analysis."
        ),
        "caveats": [
            "PAN 2012 negatives are a proxy for sensitive benign populations "
            "(peer support, LGBTQ+ youth, harm reduction); no population "
            "labels exist in the corpus, so keyword filters only capture "
            "surface-structural similarity.",
            "Keyword filters are deliberately over-inclusive and lexical; "
            "they are a sampling device, not a classifier.",
            "Substrate/control samples across seeds are drawn from the same "
            "fixed pools and overlap.",
        ],
        "figures": [
            str((OUT / "fp_substrate.pdf").relative_to(ROOT)),
            str((OUT / "fp_substrate.png").relative_to(ROOT)),
        ],
    }
    with open(OUT / "fp_substrate.json", "w") as fh:
        json.dump(output, fh, indent=2)

    # ── Figure ──────────────────────────────────────────────────────────────────
    fig, axes = plt.subplots(1, 2, figsize=(9.0, 3.6))
    for ax, det, title in ((axes[0], "minhash_16_16",
                            "MinHash signature protocol (b=16, r=16)"),
                           (axes[1], "classifier_fpr05",
                            f"Per-message LinearSVC @ FPR≤{FPR_TARGET}")):
        s = summary[det]
        means = [s["structural_FPR_mean"], s["control_FPR_mean"]]
        cis = [s["structural_FPR_pooled_wilson95"], s["control_FPR_pooled_wilson95"]]
        yerr = [[max(0.0, m - ci[0]) for m, ci in zip(means, cis)],
                [max(0.0, ci[1] - m) for m, ci in zip(means, cis)]]
        ax.bar(["structurally similar\nbenign", "random benign\ncontrol"],
               means, yerr=yerr, capsize=4,
               color=["#1f4e79", "#7f7f7f"], width=0.55)
        for i, r in enumerate(per_seed):
            ax.plot([0, 1], [r[det]["structural_FPR"], r[det]["control_FPR"]],
                    "o", color="#c00000", ms=3, alpha=0.6,
                    label="per-seed" if i == 0 else None)
        ax.set_ylabel("False positive rate")
        ax.set_title(title, fontsize=9)
        ax.grid(alpha=0.3, axis="y")
        ax.legend(fontsize=6.5, frameon=False)
    fig.suptitle(f"FP substrate: structurally similar benign vs. random benign "
                 f"(PAN 2012 test negatives, n={n_sample}/set, "
                 f"{len(SAMPLING_SEEDS)} seeds, Wilson 95% CI)", fontsize=9)
    fig.tight_layout()
    fig.savefig(OUT / "fp_substrate.pdf", bbox_inches="tight")
    fig.savefig(OUT / "fp_substrate.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print("\n=== FP substrate summary ===")
    for det in ("minhash_16_16", "classifier_fpr05"):
        s = summary[det]
        print(f"  {det}: structural={s['structural_FPR_mean']:.4f} "
              f"control={s['control_FPR_mean']:.4f} "
              f"elevated={s['elevated']}")
    print(f"\nResults: {OUT / 'fp_substrate.json'}")


if __name__ == "__main__":
    main()
