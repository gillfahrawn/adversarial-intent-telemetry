#!/usr/bin/env python3
"""
Aggregation and order controls for the RQ4 perturbation-robustness claim.

The claim under test: "the trajectory/sequence model degrades more gracefully
than the per-message baseline under discourse perturbation." That claim is
confounded if the advantage comes from conversation-level aggregation
(smoothing over many messages) rather than from trajectory/order information.
This experiment separates the two by evaluating five models/controls on the
SAME author-disjoint split, the SAME perturbed conversations, and the SAME
seeds:

  A  per_message_mean   LinearSVC message scores, conversation = mean
                        (the paper's existing baseline).
  B1 per_message_max    Same message scores, conversation = max.
  B2 per_message_top5   Same message scores, conversation = mean of top-5.
  C1 conv_concat        Order-invariant conversation classifier: TF-IDF over
                        the concatenated conversation text + LinearSVC.
  C2 conv_mean          Order-invariant twin of the sequence model: UNWEIGHTED
                        mean of message TF-IDF vectors + LogisticRegression.
                        (The sequence model is the position-WEIGHTED mean, so
                        C2 vs D isolates exactly the order information.)
  D  sequence           Position-weighted mean TF-IDF + LogisticRegression
                        (the paper's sequence model).
  E  sequence_shuffled  D scored on order-shuffled messages (per-seed RNG),
                        including at strength 0 — tests whether D uses order.

Paired statistics: for each non-zero strength and each comparison
(D vs A/B1/B2/C1/C2), a stratified paired bootstrap over test conversations
resamples positives and negatives separately (keeping AUC defined), computes
each model's AUC drop (clean-sample AUC minus perturbed-sample AUC using
seed-averaged perturbed scores), and reports the 95% CI of
(sequence drop − comparator drop). CI entirely below zero favors the
sequence model; CI containing zero means the advantage is descriptive but
not statistically resolved; CI above zero favors the comparator.

Outputs
-------
- experiments/results/perturbation_model_controls.json / .png / .pdf
- experiments/results/perturbation_paired_tests.json
- experiments/results/perturbation_sanity_checks_model_controls.json

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
from sklearn.metrics import roc_auc_score
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
    conv_to_weighted_vec, metrics_at_threshold,
)

N_PAIRED_BOOTSTRAP = 1000
TOP_K = 5

MODEL_ORDER = ["per_message_mean", "per_message_max", "per_message_top5",
               "conv_concat", "conv_mean", "sequence", "sequence_shuffled"]
MODEL_DESCRIPTIONS = {
    "per_message_mean": "LinearSVC message scores; conversation = mean "
                        "(paper baseline, order-invariant)",
    "per_message_max": "LinearSVC message scores; conversation = max "
                       "(order-invariant aggregation control)",
    "per_message_top5": f"LinearSVC message scores; conversation = mean of "
                        f"top-{TOP_K} (order-invariant aggregation control)",
    "conv_concat": "TF-IDF over concatenated conversation text + LinearSVC "
                   "(order-invariant conversation classifier)",
    "conv_mean": "Unweighted mean of message TF-IDF vectors + "
                 "LogisticRegression (order-invariant twin of the sequence "
                 "model; differs from it only by removing position weights)",
    "sequence": "Position-weighted mean of message TF-IDF vectors + "
                "LogisticRegression (paper sequence model; order-sensitive "
                "via position weights)",
    "sequence_shuffled": "sequence model scored on order-shuffled messages "
                         "(order-usage control, not a competing detector)",
}


# ── Feature/scoring helpers ─────────────────────────────────────────────────────
def concat_text(msgs) -> str:
    return " ".join(t if t else " " for _, t in msgs) or " "


def conv_to_mean_vec(msgs, vectorizer):
    texts = [t if t else " " for _, t in msgs]
    if not texts:
        return None
    X = vectorizer.transform(texts)
    return np.asarray(X.mean(axis=0))


def score_all_models(convs, models, shuffle_rng) -> dict:
    """
    Score a list of conversations (message lists) under every model.
    Each conversation's messages are TF-IDF-transformed exactly once; the
    shuffled-order sequence score is computed by permuting the position
    weights over the same rows (equivalent to shuffling the messages, since
    the weighted mean is the only order-sensitive step). Concatenated-text
    scores are computed in one batched transform.
    """
    vec, svc, concat_vec, concat_svc, lr_mean, lr_seq = (
        models["vectorizer"], models["svc"], models["concat_vectorizer"],
        models["concat_svc"], models["lr_mean"], models["lr_seq"])
    out = {name: np.empty(len(convs)) for name in MODEL_ORDER}

    # Batched conversation-concat scores
    concat_docs = [concat_text(msgs) for msgs in convs]
    out["conv_concat"][:] = concat_svc.decision_function(
        concat_vec.transform(concat_docs))

    for i, msgs in enumerate(convs):
        texts = [t if t else " " for _, t in msgs] or [" "]
        X = vec.transform(texts)
        L = X.shape[0]
        ms = svc.decision_function(X)
        out["per_message_mean"][i] = float(ms.mean())
        out["per_message_max"][i] = float(ms.max())
        k = min(TOP_K, len(ms))
        out["per_message_top5"][i] = float(np.sort(ms)[-k:].mean())

        mean_vec = np.asarray(X.mean(axis=0))
        out["conv_mean"][i] = float(lr_mean.decision_function(
            mean_vec.reshape(1, -1))[0])

        weights = np.array([1.0 + 0.5 * (j / max(L - 1, 1)) for j in range(L)])
        wv = np.asarray(X.multiply(weights[:, np.newaxis]).sum(axis=0)) / weights.sum()
        out["sequence"][i] = float(lr_seq.decision_function(wv.reshape(1, -1))[0])

        # Shuffled order == permuted position weights over the same rows
        perm = shuffle_rng.permutation(L)
        w_row = np.empty(L)
        w_row[perm] = weights
        swv = np.asarray(X.multiply(w_row[:, np.newaxis]).sum(axis=0)) / weights.sum()
        out["sequence_shuffled"][i] = float(lr_seq.decision_function(
            swv.reshape(1, -1))[0])
    return out


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

    # ── Train all models on the clean training split ────────────────────────────
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

    bank_rng = np.random.default_rng(SEED)
    benign_candidates = [txt for _, label, msgs in train if label == 0
                         for _, txt in msgs if 4 <= len(txt.split()) <= 25]
    bank_pick = bank_rng.choice(len(benign_candidates),
                                size=min(BENIGN_BANK_SIZE, len(benign_candidates)),
                                replace=False)
    benign_bank = [benign_candidates[i] for i in bank_pick]

    # ── Clean scores (positives and negatives) and fixed thresholds ────────────
    print("Scoring clean test set under all models (this is the slow step) …")
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

    # ── Sweep: score every model on every (strength, seed) ─────────────────────
    # pos_scores[strength_name][model] = list over seeds of score arrays
    pos_scores = {name: {m: [] for m in MODEL_ORDER} for name in STRENGTHS}
    sanity_conditions = []
    conditions = []

    for name, strength in STRENGTHS.items():
        seeds = [None] if strength == 0.0 else PERTURBATION_SEEDS
        per_seed_metrics = {m: [] for m in MODEL_ORDER}
        for ps in seeds:
            if strength == 0.0:
                pert_pos = [m for _, _, m in test_pos]
                op_totals = {}
            else:
                rng = np.random.default_rng(SEED + 1000 * (ps + 1))
                pert_pos, op_totals = [], {}
                for _, _, msgs in test_pos:
                    pm, ops = perturb_conversation(msgs, strength, rng, benign_bank)
                    pert_pos.append(pm)
                    for k, v in ops.items():
                        op_totals[k] = op_totals.get(k, 0) + v

            shuffle_rng = np.random.default_rng(
                SEED + 555 + (0 if ps is None else 100 * (ps + 1)))
            if strength == 0.0:
                sc = {m: clean_pos_scores[m] for m in MODEL_ORDER}
            else:
                sc = score_all_models(pert_pos, models, shuffle_rng)
            for m in MODEL_ORDER:
                pos_scores[name][m].append(np.asarray(sc[m]))
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

    # ── Degradation table and descriptive paired differences ───────────────────
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

    # ── Paired stratified bootstrap on AUC drops (Task 4) ──────────────────────
    print(f"Paired stratified bootstrap over conversations "
          f"(B={N_PAIRED_BOOTSTRAP}, seed-averaged perturbed scores) …")
    rng = np.random.default_rng(SEED + 4242)
    npos, nneg = len(pos_idx), len(neg_idx)
    comparisons = ["per_message_mean", "per_message_max", "per_message_top5",
                   "conv_concat", "conv_mean"]
    # Seed-averaged perturbed positive scores per model per strength
    seed_avg = {sname: {m: np.mean(np.vstack(pos_scores[sname][m]), axis=0)
                        for m in MODEL_ORDER}
                for sname in STRENGTHS if STRENGTHS[sname] > 0.0}

    paired = {c: {} for c in comparisons}
    for b_s in seed_avg:
        diffs = {c: np.empty(N_PAIRED_BOOTSTRAP) for c in comparisons}
        for b in range(N_PAIRED_BOOTSTRAP):
            pi = rng.integers(0, npos, size=npos)
            ni = rng.integers(0, nneg, size=nneg)
            y_b = np.concatenate([np.ones(npos, dtype=int),
                                  np.zeros(nneg, dtype=int)])
            drops = {}
            for m in set(comparisons) | {"sequence"}:
                clean_b = np.concatenate([clean_pos_scores[m][pi],
                                          neg_scores[m][ni]])
                pert_b = np.concatenate([seed_avg[b_s][m][pi],
                                         neg_scores[m][ni]])
                drops[m] = (roc_auc_score(y_b, clean_b)
                            - roc_auc_score(y_b, pert_b))
            for c in comparisons:
                diffs[c][b] = drops["sequence"] - drops[c]
        for c in comparisons:
            lo, hi = (float(np.percentile(diffs[c], 2.5)),
                      float(np.percentile(diffs[c], 97.5)))
            paired[c][b_s] = {
                "mean_diff_sequence_drop_minus_comparator_drop":
                    float(diffs[c].mean()),
                "ci95": [lo, hi],
                "ci_excludes_zero": bool(lo > 0.0 or hi < 0.0),
                "favors": ("sequence" if hi < 0.0 else
                           ("comparator" if lo > 0.0 else "unresolved")),
            }

    paired_out = {
        "experiment": "perturbation_paired_tests",
        "split_type": "author_disjoint_80_20",
        "perturbation_family": "discourse_noise",
        "perturbation_seeds": PERTURBATION_SEEDS,
        "method": ("Stratified paired bootstrap over test conversations "
                   f"(B={N_PAIRED_BOOTSTRAP}): positives and negatives "
                   "resampled separately with the same indices for every "
                   "model; perturbed positive scores averaged over the "
                   f"{len(PERTURBATION_SEEDS)} perturbation seeds before "
                   "computing AUC. diff = sequence AUC drop − comparator AUC "
                   "drop; negative diff favors the sequence model."),
        "interpretation": {
            "ci_below_zero": "sequence model's robustness advantage is "
                             "statistically resolved vs this comparator",
            "ci_contains_zero": "advantage is descriptive but not resolved",
            "ci_above_zero": "comparator is more robust; trajectory claim "
                             "weakened vs this comparator",
        },
        "comparisons": paired,
    }
    with open(OUT / "perturbation_paired_tests.json", "w") as fh:
        json.dump(paired_out, fh, indent=2)

    # ── Main JSON ────────────────────────────────────────────────────────────────
    output = {
        "experiment": "perturbation_model_controls",
        "dataset": "PAN 2012 SPI training XML, author-disjoint 80/20 split "
                   "(same as exp_m3_author_split.py)",
        "split_type": "author_disjoint_80_20",
        "split_seed": SEED,
        "perturbation_family": "discourse_noise "
                               "(truncate/benign-swap/drop + adjacent order jitter)",
        "perturbation_seeds": PERTURBATION_SEEDS,
        "threat_model": "test positives perturbed at inference; negatives clean; "
                        "per-model thresholds calibrated once on clean test at "
                        f"FPR<={FPR_TARGET} and held fixed",
        "n_test_conversations": len(test),
        "n_test_positives": int(npos),
        "n_test_negatives": int(nneg),
        "models": MODEL_DESCRIPTIONS,
        "thresholds": thresholds,
        "conditions": conditions,
        "degradation": degradation,
        "notes": [
            "sequence_shuffled is an order-usage control for the sequence "
            "model, not a competing detector; its clean condition is also "
            "shuffled.",
            "conv_mean differs from sequence only by removing position "
            "weights, so (sequence - conv_mean) isolates order information.",
            "Paired statistical comparison is in perturbation_paired_tests.json.",
        ],
        "figures": [
            str((OUT / "perturbation_model_controls.pdf").relative_to(ROOT)),
            str((OUT / "perturbation_model_controls.png").relative_to(ROOT)),
        ],
    }
    with open(OUT / "perturbation_model_controls.json", "w") as fh:
        json.dump(output, fh, indent=2)

    sanity = {
        "experiment": "perturbation_sanity_checks_model_controls",
        "source": "exp_perturbation_model_controls.py (first seed per strength)",
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
                   "label_balance": {"positives": int(npos),
                                     "negatives": int(nneg)}},
        "metadata_fields": {"changed": False},
        "text_surface": {"changed_for_nonzero_strengths": True,
                         "family": "discourse_noise (same as "
                                   "perturbation_sweep.json)"},
        "identical_perturbed_conversations_across_models": True,
        "no_raw_text_in_outputs": True,
        "per_condition": sanity_conditions,
    }
    with open(OUT / "perturbation_sanity_checks_model_controls.json", "w") as fh:
        json.dump(sanity, fh, indent=2)

    # ── Figure: AUC vs strength for all models ──────────────────────────────────
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
    ax.set_xlabel("Perturbation strength (discourse noise)")
    ax.set_ylabel("AUC (mean ± std over 5 seeds)")
    ax.set_title("Aggregation/order controls under perturbation — "
                 "author-disjoint split", fontsize=10)
    ax.grid(alpha=0.3)
    ax.legend(fontsize=7, frameon=False)
    fig.tight_layout()
    fig.savefig(OUT / "perturbation_model_controls.pdf", bbox_inches="tight")
    fig.savefig(OUT / "perturbation_model_controls.png", dpi=150,
                bbox_inches="tight")
    plt.close(fig)

    print("\n=== Degradation (AUC drop from clean, mean over seeds) ===")
    for row in degradation:
        print(f"  [{row['strength_name']:6s}] " + "  ".join(
            f"{m}={row['models'][m]['auc_drop']:+.4f}" for m in MODEL_ORDER))
    print("\n=== Paired bootstrap (sequence drop − comparator drop) ===")
    for c in comparisons:
        for s, r in paired[c].items():
            print(f"  vs {c:18s} [{s:6s}] mean={r['mean_diff_sequence_drop_minus_comparator_drop']:+.4f} "
                  f"CI={r['ci95']}  favors={r['favors']}")
    print(f"\nResults: {OUT / 'perturbation_model_controls.json'}")
    print(f"Paired:  {OUT / 'perturbation_paired_tests.json'}")


if __name__ == "__main__":
    main()
