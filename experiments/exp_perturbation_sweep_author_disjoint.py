#!/usr/bin/env python3
"""
Author-disjoint replication of the discourse-noise perturbation sweep (RQ4).

The original sweep (exp_perturbation_sweep.py) uses the 80/20 stratified
conversation-level split, which allows a predator author's conversations to
appear on both sides. This replication uses the author-disjoint split from
exp_m3_author_split.py: no predator author appears in both train and test
(conversations whose predator authors span both partitions go to test,
conservatively). Benign-only conversations, which have no predator author,
are split 80/20 by conversation ID with the same seeded RNG — documented in
author_disjoint_split()'s docstring.

Everything else replicates the original sweep exactly: same models, same
discourse-noise family (truncate / benign-swap / drop + adjacent order
jitter), same strengths (none / light 0.15 / medium 0.35 / heavy 0.60), same
5 perturbation seeds, thresholds calibrated once on the clean test set at
FPR <= 0.05 and held fixed. The claim under test can be strengthened OR
overturned by this replication; the verdict logic does not assume a
direction.

Outputs
-------
- experiments/results/perturbation_sweep_author_disjoint.json
- experiments/results/perturbation_sweep_author_disjoint.png / .pdf
- experiments/results/perturbation_sanity_checks_author_disjoint.json

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
from exp_m3_author_split import (  # noqa: E402
    SEED, DATA_XML, DATA_PRED,
    load_predators, parse_pan12, author_disjoint_split,
)
from exp_trajectory_lift import operating_point_at_fpr  # noqa: E402
from exp_perturbation_sweep import (  # noqa: E402
    PERTURBATION_SEEDS, STRENGTHS, FPR_TARGET, BENIGN_BANK_SIZE,
    perturb_conversation, token_set, jaccard, sha256_ids,
    score_baseline, score_sequence, conv_to_weighted_vec,
    metrics_at_threshold, bootstrap_auc_ci,
)


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
    train, test, train_authors, test_authors, _ = author_disjoint_split(
        conversations, predators)
    author_overlap = sorted(set(train_authors) & set(test_authors))
    assert not author_overlap, f"author overlap in split: {author_overlap}"

    y_test = np.array([label for _, label, _ in test], dtype=int)
    pos_idx = np.where(y_test == 1)[0]
    neg_idx = np.where(y_test == 0)[0]
    print(f"  author-disjoint split: train={len(train)}  test={len(test)} "
          f"(pos={len(pos_idx)}, neg={len(neg_idx)}); "
          f"predator authors train={len(train_authors)} test={len(test_authors)}, "
          f"overlap={len(author_overlap)}")

    print("Fitting TF-IDF + training both models on clean training data …")
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

    X_rows, y_rows = [], []
    for _, label, msgs in train:
        vec = conv_to_weighted_vec(msgs, vectorizer)
        if vec is not None:
            X_rows.append(vec.flatten())
            y_rows.append(label)
    lr = LogisticRegression(C=1.0, max_iter=1000, random_state=SEED)
    lr.fit(np.vstack(X_rows), np.array(y_rows, dtype=int))

    bank_rng = np.random.default_rng(SEED)
    benign_candidates = [txt for _, label, msgs in train if label == 0
                         for _, txt in msgs if 4 <= len(txt.split()) <= 25]
    bank_pick = bank_rng.choice(len(benign_candidates),
                                size=min(BENIGN_BANK_SIZE, len(benign_candidates)),
                                replace=False)
    benign_bank = [benign_candidates[i] for i in bank_pick]
    print(f"  Benign swap bank: {len(benign_bank)} training-split benign messages")

    print("Scoring clean test set (both models) …")
    base_clean = np.array([score_baseline(m, vectorizer, svc) for _, _, m in test])
    seq_clean = np.array([score_sequence(m, vectorizer, lr) for _, _, m in test])
    base_thr, *_ = operating_point_at_fpr(y_test, base_clean, FPR_TARGET)
    seq_thr, *_ = operating_point_at_fpr(y_test, seq_clean, FPR_TARGET)

    base_neg_scores = base_clean[neg_idx]
    seq_neg_scores = seq_clean[neg_idx]
    test_pos = [test[i] for i in pos_idx]

    conditions = []
    sanity_conditions = []
    orig_token_sets = [token_set(m) for _, _, m in test_pos]
    orig_msg_counts = [len(m) for _, _, m in test_pos]
    orig_word_means = [float(np.mean([len(t.split()) for _, t in m])) if m else 0.0
                       for _, _, m in test_pos]

    for name, strength in STRENGTHS.items():
        seeds = [None] if strength == 0.0 else PERTURBATION_SEEDS
        per_seed = []
        for ps in seeds:
            if strength == 0.0:
                pert_pos = [m for _, _, m in test_pos]
                op_totals = {"kept": sum(orig_msg_counts), "truncated": 0,
                             "swapped_benign": 0, "dropped": 0,
                             "adjacent_transpositions": 0, "drop_guard_hits": 0}
            else:
                rng = np.random.default_rng(SEED + 1000 * (ps + 1))
                pert_pos, op_totals = [], {}
                for _, _, msgs in test_pos:
                    pm, ops = perturb_conversation(msgs, strength, rng, benign_bank)
                    pert_pos.append(pm)
                    for k, v in ops.items():
                        op_totals[k] = op_totals.get(k, 0) + v

            base_pos = np.array([score_baseline(m, vectorizer, svc) for m in pert_pos])
            seq_pos = np.array([score_sequence(m, vectorizer, lr) for m in pert_pos])

            y_all = np.concatenate([np.ones(len(pos_idx), dtype=int),
                                    np.zeros(len(neg_idx), dtype=int)])
            base_all = np.concatenate([base_pos, base_neg_scores])
            seq_all = np.concatenate([seq_pos, seq_neg_scores])

            row = {
                "perturbation_seed": ps,
                "baseline": metrics_at_threshold(y_all, base_all, base_thr),
                "sequence": metrics_at_threshold(y_all, seq_all, seq_thr),
                "op_totals": op_totals,
            }
            if ps in (None, PERTURBATION_SEEDS[0]):
                row["baseline"]["auc_bootstrap_95ci"] = bootstrap_auc_ci(y_all, base_all)
                row["sequence"]["auc_bootstrap_95ci"] = bootstrap_auc_ci(y_all, seq_all)
            per_seed.append(row)

            if ps in (None, PERTURBATION_SEEDS[0]):
                jac = [jaccard(orig_token_sets[i], token_set(pert_pos[i]))
                       for i in range(len(pert_pos))]
                order_changed = 0
                for i, (_, _, orig_msgs) in enumerate(test_pos):
                    surviving = [t for _, t in pert_pos[i]]
                    orig_texts = [t for _, t in orig_msgs]
                    it = iter(orig_texts)
                    is_subseq = all(any(s == o for o in it) for s in surviving)
                    if not is_subseq or op_totals.get("adjacent_transpositions", 0) > 0:
                        order_changed += 1
                pert_msg_counts = [len(m) for m in pert_pos]
                pert_word_means = [float(np.mean([len(t.split()) for _, t in m]))
                                   if m else 0.0 for m in pert_pos]
                total_msgs = sum(orig_msg_counts)
                n_modified = (op_totals.get("truncated", 0)
                              + op_totals.get("swapped_benign", 0)
                              + op_totals.get("dropped", 0))
                sanity_conditions.append({
                    "strength_name": name,
                    "strength": strength,
                    "seed": ps,
                    "labels_unchanged": True,
                    "n_test_conversations_unchanged": len(pert_pos) == len(test_pos),
                    "fraction_messages_modified": n_modified / max(total_msgs, 1),
                    "mean_token_jaccard_original_vs_perturbed": float(np.mean(jac)),
                    "median_token_jaccard": float(np.median(jac)),
                    "fraction_conversations_order_changed":
                        order_changed / max(len(pert_pos), 1),
                    "mean_messages_per_conversation":
                        {"before": float(np.mean(orig_msg_counts)),
                         "after": float(np.mean(pert_msg_counts))},
                    "mean_words_per_message":
                        {"before": float(np.mean(orig_word_means)),
                         "after": float(np.mean(pert_word_means))},
                    "op_totals": op_totals,
                })

        def agg(model_key, metric):
            vals = np.array([r[model_key][metric] for r in per_seed])
            out = {"mean": float(vals.mean()), "std": float(vals.std(ddof=0)),
                   "min": float(vals.min()), "max": float(vals.max()),
                   "per_seed": [float(v) for v in vals]}
            if len(vals) > 1:
                se = vals.std(ddof=1) / np.sqrt(len(vals))
                out["across_seed_95ci"] = [float(vals.mean() - 1.96 * se),
                                           float(vals.mean() + 1.96 * se)]
            return out

        cond = {
            "strength_name": name,
            "strength": strength,
            "perturbation_type": "discourse_noise "
                                 "(truncate/benign-swap/drop + adjacent order jitter)",
            "seeds": [s for s in seeds if s is not None] or ["deterministic"],
            "n_seeds": len(per_seed),
            "baseline": {m: agg("baseline", m)
                         for m in ("auc", "f1", "precision", "recall", "fpr", "accuracy")},
            "sequence": {m: agg("sequence", m)
                         for m in ("auc", "f1", "precision", "recall", "fpr", "accuracy")},
            "auc_bootstrap_95ci_first_seed": {
                "baseline": per_seed[0]["baseline"].get("auc_bootstrap_95ci"),
                "sequence": per_seed[0]["sequence"].get("auc_bootstrap_95ci"),
            },
        }
        conditions.append(cond)
        b, s = cond["baseline"], cond["sequence"]
        print(f"  [{name:6s} s={strength:.2f}] "
              f"base AUC={b['auc']['mean']:.3f}±{b['auc']['std']:.3f} "
              f"recall={b['recall']['mean']:.3f} | "
              f"seq AUC={s['auc']['mean']:.3f}±{s['auc']['std']:.3f} "
              f"recall={s['recall']['mean']:.3f}")

    clean = conditions[0]
    verdict_rows = []
    for cond in conditions[1:]:
        d_base = clean["baseline"]["auc"]["mean"] - cond["baseline"]["auc"]["mean"]
        d_seq = clean["sequence"]["auc"]["mean"] - cond["sequence"]["auc"]["mean"]
        verdict_rows.append({
            "strength_name": cond["strength_name"],
            "baseline_auc_drop": float(d_base),
            "sequence_auc_drop": float(d_seq),
            "sequence_degrades_less": bool(d_seq < d_base),
        })
    n_graceful = sum(r["sequence_degrades_less"] for r in verdict_rows)
    verdict = {
        "claim": "sequence model degrades more gracefully than per-message "
                 "baseline under discourse perturbation (author-disjoint split)",
        "criterion": "sequence AUC drop < baseline AUC drop (mean over seeds) "
                     "at >= 2 of 3 non-zero strengths",
        "per_strength": verdict_rows,
        "n_strengths_where_sequence_degrades_less": n_graceful,
        "supported": bool(n_graceful >= 2),
        "scope_caveat": "Within this discourse-noise family only; see "
                        "exp_perturbation_model_controls.py for the "
                        "aggregation/order-control comparison.",
    }

    output = {
        "experiment": "perturbation_sweep_author_disjoint",
        "dataset": "PAN 2012 SPI training XML, author-disjoint 80/20 split "
                   "(same as exp_m3_author_split.py)",
        "split_type": "author_disjoint_80_20",
        "split_seed": SEED,
        "benign_assignment": "Benign conversations have no predator author; "
                             "they are split 80/20 by conversation ID with the "
                             "same seeded RNG (see author_disjoint_split()).",
        "predator_authors": {"train": len(train_authors),
                             "test": len(test_authors),
                             "overlap": len(author_overlap)},
        "perturbation_seeds": PERTURBATION_SEEDS,
        "perturbation_family": "discourse_noise",
        "threat_model": "test positives perturbed at inference; negatives clean; "
                        "thresholds calibrated once on clean test at "
                        f"FPR<={FPR_TARGET} and held fixed",
        "n_test_conversations": len(test),
        "n_test_positives": int(len(pos_idx)),
        "n_test_negatives": int(len(neg_idx)),
        "n_test_messages_positives": int(sum(orig_msg_counts)),
        "models": {
            "baseline": "LinearSVC per-message, mean decision value",
            "sequence": "LogisticRegression on position-weighted mean TF-IDF vector",
        },
        "thresholds": {"baseline": float(base_thr), "sequence": float(seq_thr)},
        "conditions": conditions,
        "verdict": verdict,
        "caveats": [
            "Author-disjoint replication of perturbation_sweep.json; compare "
            "the two verdicts before quoting either.",
            "Perturbation family is limited (truncate/benign-swap/drop/adjacent "
            "jitter); no paraphrase or feature-aware evasion is included.",
            "PAN 2012 validates 2012 human grooming, not 2026 agentic automation.",
        ],
        "figures": [
            str((OUT / "perturbation_sweep_author_disjoint.pdf").relative_to(ROOT)),
            str((OUT / "perturbation_sweep_author_disjoint.png").relative_to(ROOT)),
        ],
    }
    with open(OUT / "perturbation_sweep_author_disjoint.json", "w") as fh:
        json.dump(output, fh, indent=2)

    sanity = {
        "experiment": "perturbation_sanity_checks_author_disjoint",
        "source": "exp_perturbation_sweep_author_disjoint.py "
                  "(first seed of each strength)",
        "split_hash_sha256": {
            "train_conversation_ids": sha256_ids(train),
            "test_conversation_ids": sha256_ids(test),
            "note": "Perturbation is applied after the split; the split is "
                    "identical for every condition by construction.",
        },
        "author_disjointness": {
            "n_train_predator_authors": len(train_authors),
            "n_test_predator_authors": len(test_authors),
            "n_overlapping_authors": len(author_overlap),
            "disjoint": len(author_overlap) == 0,
        },
        "labels": {
            "unchanged": True,
            "note": "y_test held fixed; perturbation never adds/removes "
                    "conversations (drop guard keeps >= max(3, 25%) messages).",
            "label_balance": {"positives": int(len(pos_idx)),
                              "negatives": int(len(neg_idx))},
        },
        "metadata_fields": {
            "changed": False,
            "note": "Author IDs preserved on surviving messages; no other "
                    "metadata/telemetry fields exist in the pipeline.",
        },
        "text_surface": {
            "changed_for_nonzero_strengths": True,
            "how_and_why": "Same discourse-noise family as "
                           "perturbation_sweep.json (truncate, benign-swap, "
                           "drop, adjacent transpositions), test positives only.",
        },
        "no_raw_text_in_outputs": True,
        "per_condition": sanity_conditions,
    }
    with open(OUT / "perturbation_sanity_checks_author_disjoint.json", "w") as fh:
        json.dump(sanity, fh, indent=2)

    xs = [c["strength"] for c in conditions]
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(9.2, 3.6))
    for ax, metric, title in ((ax1, "auc", "AUC (threshold-free)"),
                              (ax2, "recall", f"Recall at fixed clean "
                                              f"FPR≤{FPR_TARGET} threshold")):
        for model, color, marker, lbl in (("baseline", "#7f7f7f", "o",
                                           "Per-message LinearSVC"),
                                          ("sequence", "#1f4e79", "^",
                                           "Sequence (pos-weighted LogReg)")):
            means = [c[model][metric]["mean"] for c in conditions]
            stds = [c[model][metric]["std"] for c in conditions]
            ax.errorbar(xs, means, yerr=stds, color=color, marker=marker,
                        lw=1.4, ms=5, capsize=3, label=lbl)
        if metric == "auc":
            ax.axhline(0.5, color="#c00000", lw=0.7, ls=":", alpha=0.6,
                       label="Random (AUC=0.5)")
        ax.set_xlabel("Perturbation strength")
        ax.set_ylabel(metric.upper() if metric == "auc" else "Recall")
        ax.set_title(title, fontsize=9)
        ax.grid(alpha=0.3)
        ax.legend(fontsize=6.5, frameon=False)
    fig.suptitle("Discourse-noise perturbation sweep — author-disjoint split "
                 f"(positives perturbed, negatives clean; "
                 f"{len(PERTURBATION_SEEDS)} seeds)", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(OUT / "perturbation_sweep_author_disjoint.pdf", bbox_inches="tight")
    fig.savefig(OUT / "perturbation_sweep_author_disjoint.png", dpi=150,
                bbox_inches="tight")
    plt.close(fig)

    print("\n=== Author-disjoint perturbation sweep verdict ===")
    for r in verdict_rows:
        print(f"  {r['strength_name']:6s}: baseline AUC drop {r['baseline_auc_drop']:+.3f}"
              f"  sequence AUC drop {r['sequence_auc_drop']:+.3f}"
              f"  -> sequence degrades less: {r['sequence_degrades_less']}")
    print(f"  Claim supported (>=2/3 strengths): {verdict['supported']}")
    print(f"\nResults: {OUT / 'perturbation_sweep_author_disjoint.json'}")


if __name__ == "__main__":
    main()
