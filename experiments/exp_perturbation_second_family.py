#!/usr/bin/env python3
"""
Second perturbation family (surface_rewrite_rule_based) under the same
model-control framework as exp_perturbation_model_controls.py.

The discourse-noise family removes/replaces message content; this family
(tools/inject_surface_rewrite_noise.py) preserves content and order while
rewriting surface form (chat-register substitutions, casing/punctuation
jitter) and message segmentation (split/merge). It attacks the character
n-gram features directly, which is the natural complement to discourse noise
and a harder test for the per-message baseline's surface features.

Same author-disjoint split, same strengths (none/0.15/0.35/0.60), same 5
seeds, same seven models/controls, per-model thresholds calibrated once on
the clean test set at FPR <= 0.05 and held fixed.

Outputs
-------
- experiments/results/perturbation_second_family.json / .png / .pdf
- experiments/results/perturbation_sanity_checks_second_family.json

No raw PAN message text is printed or written to any output.
"""

import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC

SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
OUT = SCRIPT_DIR / "results"
OUT.mkdir(parents=True, exist_ok=True)

sys.path.insert(0, str(SCRIPT_DIR))
sys.path.insert(0, str(ROOT / "tools"))
from exp_m3_author_split import (  # noqa: E402
    SEED, DATA_XML, DATA_PRED,
    load_predators, parse_pan12, author_disjoint_split,
)
from exp_trajectory_lift import operating_point_at_fpr  # noqa: E402
from exp_perturbation_sweep import (  # noqa: E402
    PERTURBATION_SEEDS, STRENGTHS, FPR_TARGET,
    token_set, jaccard, sha256_ids, conv_to_weighted_vec, metrics_at_threshold,
)
from exp_perturbation_model_controls import (  # noqa: E402
    MODEL_ORDER, MODEL_DESCRIPTIONS, concat_text, conv_to_mean_vec,
    score_all_models,
)
from inject_surface_rewrite_noise import (  # noqa: E402
    perturb_conversation_surface, FAMILY_NAME, SUBSTITUTIONS,
)


def main() -> None:
    missing = [p for p in (DATA_XML, DATA_PRED) if not p.exists()]
    if missing:
        print("ERROR: Required PAN 2012 data files not found:", file=sys.stderr)
        for p in missing:
            print(f"  {p}", file=sys.stderr)
        print("\nSee data/pan12/README.md for how to obtain PAN 2012, then place "
              "the training XML\nand predator list in data/pan12/train/ and re-run.",
              file=sys.stderr)
        sys.exit(1)

    print("Parsing PAN 2012 XML …")
    predators = load_predators(DATA_PRED)
    conversations = parse_pan12(DATA_XML, predators)
    train, test, train_authors, test_authors, _ = author_disjoint_split(
        conversations, predators)
    author_overlap = sorted(set(train_authors) & set(test_authors))
    assert not author_overlap, f"author overlap in split: {author_overlap}"

    y_test = np.array([label for _, label, _ in test], dtype=int)
    pos_idx = np.where(y_test == 1)[0]
    neg_idx = np.where(y_test == 0)[0]
    print(f"  author-disjoint split: train={len(train)}  test={len(test)} "
          f"(pos={len(pos_idx)}, neg={len(neg_idx)})")

    # ── Train the same model set as exp_perturbation_model_controls.py ─────────
    print("Training message-level LinearSVC …")
    train_msg_texts, train_msg_labels = [], []
    for _, label, msgs in train:
        for _, txt in msgs:
            train_msg_texts.append(txt if txt else " ")
            train_msg_labels.append(label)
    vectorizer = TfidfVectorizer(max_features=10_000, analyzer="char_wb",
                                 ngram_range=(3, 5), sublinear_tf=True)
    vectorizer.fit(train_msg_texts)
    svc = LinearSVC(random_state=SEED)
    svc.fit(vectorizer.transform(train_msg_texts),
            np.array(train_msg_labels, dtype=int))

    print("Training conversation-concat LinearSVC …")
    concat_vectorizer = TfidfVectorizer(max_features=10_000, analyzer="char_wb",
                                        ngram_range=(3, 5), sublinear_tf=True)
    train_concat = [concat_text(msgs) for _, _, msgs in train]
    y_train_conv = np.array([label for _, label, _ in train], dtype=int)
    concat_vectorizer.fit(train_concat)
    concat_svc = LinearSVC(random_state=SEED)
    concat_svc.fit(concat_vectorizer.transform(train_concat), y_train_conv)

    print("Training conv-mean and sequence LogisticRegressions …")
    Xm_rows, Xw_rows, y_rows = [], [], []
    for _, label, msgs in train:
        mv = conv_to_mean_vec(msgs, vectorizer)
        wv = conv_to_weighted_vec(msgs, vectorizer)
        if mv is not None and wv is not None:
            Xm_rows.append(mv.flatten())
            Xw_rows.append(wv.flatten())
            y_rows.append(label)
    y_conv = np.array(y_rows, dtype=int)
    lr_mean = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
    lr_mean.fit(np.vstack(Xm_rows), y_conv)
    lr_seq = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
    lr_seq.fit(np.vstack(Xw_rows), y_conv)

    models = {"vectorizer": vectorizer, "svc": svc,
              "concat_vectorizer": concat_vectorizer, "concat_svc": concat_svc,
              "lr_mean": lr_mean, "lr_seq": lr_seq}

    print("Scoring clean test set under all models …")
    shuffle_rng_clean = np.random.default_rng(SEED + 777)
    clean_scores = score_all_models([m for _, _, m in test], models,
                                    shuffle_rng_clean)
    thresholds = {}
    for name in MODEL_ORDER:
        thr, *_ = operating_point_at_fpr(y_test, clean_scores[name], FPR_TARGET)
        thresholds[name] = float(thr)
    neg_scores = {name: clean_scores[name][neg_idx] for name in MODEL_ORDER}
    clean_pos_scores = {name: clean_scores[name][pos_idx] for name in MODEL_ORDER}
    test_pos = [test[i] for i in pos_idx]
    orig_msg_counts = [len(m) for _, _, m in test_pos]
    orig_token_sets = [token_set(m) for _, _, m in test_pos]

    y_all = np.concatenate([np.ones(len(pos_idx), dtype=int),
                            np.zeros(len(neg_idx), dtype=int)])

    conditions = []
    sanity_conditions = []
    for name, strength in STRENGTHS.items():
        seeds = [None] if strength == 0.0 else PERTURBATION_SEEDS
        per_seed_metrics = {m: [] for m in MODEL_ORDER}
        for ps in seeds:
            if strength == 0.0:
                pert_pos = [m for _, _, m in test_pos]
                op_totals = {}
                sc = {m: clean_pos_scores[m] for m in MODEL_ORDER}
            else:
                rng = np.random.default_rng(SEED + 2000 * (ps + 1))
                pert_pos, op_totals = [], {}
                for _, _, msgs in test_pos:
                    pm, ops = perturb_conversation_surface(msgs, strength, rng)
                    pert_pos.append(pm)
                    for k, v in ops.items():
                        op_totals[k] = op_totals.get(k, 0) + v
                shuffle_rng = np.random.default_rng(SEED + 555 + 100 * (ps + 1))
                sc = score_all_models(pert_pos, models, shuffle_rng)
            for m in MODEL_ORDER:
                all_scores = np.concatenate([sc[m], neg_scores[m]])
                per_seed_metrics[m].append(
                    metrics_at_threshold(y_all, all_scores, thresholds[m]))

            if ps in (None, PERTURBATION_SEEDS[0]):
                jac = [jaccard(orig_token_sets[i], token_set(pert_pos[i]))
                       for i in range(len(pert_pos))]
                sanity_conditions.append({
                    "strength_name": name, "strength": strength, "seed": ps,
                    "labels_unchanged": True,
                    "n_test_conversations_unchanged": len(pert_pos) == len(test_pos),
                    "mean_token_jaccard_original_vs_perturbed": float(np.mean(jac)),
                    "mean_messages_per_conversation":
                        {"before": float(np.mean(orig_msg_counts)),
                         "after": float(np.mean([len(m) for m in pert_pos]))},
                    "note": "Message count may change via split/merge ops; "
                            "conversation count and labels never change. "
                            "Token Jaccard < 1 reflects register "
                            "substitutions only.",
                    "op_totals": op_totals,
                })

        def agg(model, metric):
            vals = np.array([r[metric] for r in per_seed_metrics[model]])
            out = {"mean": float(vals.mean()), "std": float(vals.std(ddof=0)),
                   "per_seed": [float(v) for v in vals]}
            if len(vals) > 1:
                se = vals.std(ddof=1) / np.sqrt(len(vals))
                out["across_seed_95ci"] = [float(vals.mean() - 1.96 * se),
                                           float(vals.mean() + 1.96 * se)]
            return out

        cond = {"strength_name": name, "strength": strength,
                "seeds": [s for s in seeds if s is not None] or ["deterministic"]}
        for m in MODEL_ORDER:
            cond[m] = {metric: agg(m, metric)
                       for metric in ("auc", "f1", "precision", "recall", "accuracy")}
        conditions.append(cond)
        print(f"  [{name:6s}] " + "  ".join(
            f"{m}={cond[m]['auc']['mean']:.3f}" for m in MODEL_ORDER))

    clean_cond = conditions[0]
    degradation = []
    for cond in conditions[1:]:
        row = {"strength_name": cond["strength_name"],
               "strength": cond["strength"], "models": {}}
        seq_drop = (clean_cond["sequence"]["auc"]["mean"]
                    - cond["sequence"]["auc"]["mean"])
        for m in MODEL_ORDER:
            drop = clean_cond[m]["auc"]["mean"] - cond[m]["auc"]["mean"]
            row["models"][m] = {
                "auc_clean": clean_cond[m]["auc"]["mean"],
                "auc_perturbed_mean": cond[m]["auc"]["mean"],
                "auc_drop": float(drop),
                "sequence_drop_minus_this_drop": float(seq_drop - drop),
            }
        degradation.append(row)

    output = {
        "experiment": "perturbation_second_family",
        "perturbation_family": FAMILY_NAME,
        "family_description": "Rule-based surface rewrite + segmentation "
                              "noise: bidirectional chat-register "
                              "substitutions from a fixed neutral table "
                              f"({len(SUBSTITUTIONS)//2} pairs), "
                              "casing/punctuation jitter, message split/merge. "
                              "Content-preserving; complements discourse noise.",
        "dataset": "PAN 2012 SPI training XML, author-disjoint 80/20 split",
        "split_type": "author_disjoint_80_20",
        "split_seed": SEED,
        "perturbation_seeds": PERTURBATION_SEEDS,
        "threat_model": "test positives perturbed at inference; negatives clean; "
                        "per-model thresholds calibrated once on clean test at "
                        f"FPR<={FPR_TARGET} and held fixed",
        "n_test_conversations": len(test),
        "n_test_positives": int(len(pos_idx)),
        "n_test_negatives": int(len(neg_idx)),
        "models": MODEL_DESCRIPTIONS,
        "thresholds": thresholds,
        "conditions": conditions,
        "degradation": degradation,
        "figures": [
            str((OUT / "perturbation_second_family.pdf").relative_to(ROOT)),
            str((OUT / "perturbation_second_family.png").relative_to(ROOT)),
        ],
    }
    with open(OUT / "perturbation_second_family.json", "w") as fh:
        json.dump(output, fh, indent=2)

    sanity = {
        "experiment": "perturbation_sanity_checks_second_family",
        "source": "exp_perturbation_second_family.py (first seed per strength)",
        "split_hash_sha256": {
            "train_conversation_ids": sha256_ids(train),
            "test_conversation_ids": sha256_ids(test),
        },
        "author_disjointness": {
            "n_train_predator_authors": len(train_authors),
            "n_test_predator_authors": len(test_authors),
            "n_overlapping_authors": len(author_overlap),
            "disjoint": len(author_overlap) == 0,
        },
        "labels": {"unchanged": True,
                   "label_balance": {"positives": int(len(pos_idx)),
                                     "negatives": int(len(neg_idx))}},
        "metadata_fields": {"changed": False,
                            "note": "Author IDs preserved, including through "
                                    "split/merge ops."},
        "text_surface": {"changed_for_nonzero_strengths": True,
                         "family": FAMILY_NAME,
                         "how": "register substitutions, casing/punctuation "
                                "jitter, message split/merge; no content "
                                "generated, no messages dropped or swapped."},
        "order_changed": "Message order is preserved except where split/merge "
                         "changes segmentation locally; no transpositions.",
        "no_raw_text_in_outputs": True,
        "per_condition": sanity_conditions,
    }
    with open(OUT / "perturbation_sanity_checks_second_family.json", "w") as fh:
        json.dump(sanity, fh, indent=2)

    xs = [c["strength"] for c in conditions]
    colors = {"per_message_mean": "#7f7f7f", "per_message_max": "#b0b0b0",
              "per_message_top5": "#d0a000", "conv_concat": "#2e7d32",
              "conv_mean": "#c00000", "sequence": "#1f4e79",
              "sequence_shuffled": "#7b1fa2"}
    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    for m in MODEL_ORDER:
        means = [c[m]["auc"]["mean"] for c in conditions]
        stds = [c[m]["auc"]["std"] for c in conditions]
        ax.errorbar(xs, means, yerr=stds, marker="o", ms=4, lw=1.3, capsize=3,
                    color=colors[m], label=m,
                    ls="--" if m == "sequence_shuffled" else "-")
    ax.set_xlabel(f"Perturbation strength ({FAMILY_NAME})")
    ax.set_ylabel("AUC (mean ± std over 5 seeds)")
    ax.set_title("Second perturbation family — author-disjoint split",
                 fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "perturbation_second_family.pdf", bbox_inches="tight")
    fig.savefig(OUT / "perturbation_second_family.png", dpi=150,
                bbox_inches="tight")
    plt.close(fig)

    print("\n=== Degradation (AUC drop from clean, mean over seeds) ===")
    for row in degradation:
        print(f"  [{row['strength_name']:6s}] " + "  ".join(
            f"{m}={row['models'][m]['auc_drop']:+.4f}" for m in MODEL_ORDER))
    print(f"\nResults: {OUT / 'perturbation_second_family.json'}")


if __name__ == "__main__":
    main()
