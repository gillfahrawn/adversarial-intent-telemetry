#!/usr/bin/env python3
"""
Perturbation sweep: per-message baseline vs. sequence model under
discourse-noise perturbation at multiple strengths and seeds.

Target claim under test (README): "Trajectory-level structure does not beat a
strong per-message baseline on clean PAN 2012, but it may degrade more
gracefully under adaptive/discourse perturbation." This script is designed to
strengthen OR falsify that claim, not to confirm it.

Design
------
- Models and split are identical to exp_trajectory_lift.py: PAN 2012 training
  XML, 80/20 stratified conversation-level split (NOT author-disjoint; the
  author-disjoint split is used by the MinHash experiments), TF-IDF char_wb
  (3,5) features, per-message LinearSVC baseline (conversation score = mean
  message decision value), position-weighted-average LogisticRegression
  sequence model. Both models are trained once on clean training data.
- Threat model: an adaptive adversary perturbs the discourse of *positive*
  (grooming) conversations at inference time; benign traffic is unchanged.
  Test negatives are therefore left clean, and detection thresholds are
  calibrated once on the clean test set at FPR <= 0.05, then held fixed
  across perturbation strengths (deployment-realistic: the defender does not
  re-calibrate per attack).
- Perturbation family ("discourse noise", mirroring the ops in
  tools/inject_discourse_noise.py): per message, with probability = strength,
  one of {truncate (0.4), benign-swap (0.4), drop (0.2)}; plus
  strength-proportional adjacent-transposition order jitter. Benign-swap
  replaces a message's text with a message sampled from *training-split
  benign* conversations (processed locally; never printed). A drop guard
  keeps at least max(3, 25%) of each conversation's messages.
- Strengths: none=0.0, light=0.15, medium=0.35, heavy=0.60.
- Seeds: 5 perturbation seeds per non-zero strength. Training/split seed is
  fixed (SEED=20260514, as in all other experiments) so that variance
  reported here is perturbation variance, not split variance.

This perturbation family is limited and not exhaustive: it does not include
paraphrase attacks, deliberate feature-aware evasion, persona splitting, or
cross-platform migration. Conclusions are scoped to this family.

Outputs
-------
- experiments/results/perturbation_sweep.json
- experiments/results/perturbation_sweep.png / .pdf
- experiments/results/perturbation_sanity_checks.json

No raw PAN message text is printed or written to any output.
"""

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score, roc_curve
from sklearn.svm import LinearSVC

# ── Reproducibility ────────────────────────────────────────────────────────────
SEED = 20260514
PERTURBATION_SEEDS = [0, 1, 2, 3, 4]

# ── Paths ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).parent
ROOT = SCRIPT_DIR.parent
OUT = SCRIPT_DIR / "results"
OUT.mkdir(parents=True, exist_ok=True)

DATA_XML = (ROOT / "data/pan12/train/"
            "pan12-sexual-predator-identification-training-corpus-2012-05-01.xml")
DATA_PRED = (ROOT / "data/pan12/train/"
             "pan12-sexual-predator-identification-training-corpus-predators-2012-05-01.txt")

FPR_TARGET = 0.05
N_BOOTSTRAP = 500

STRENGTHS = {"none": 0.0, "light": 0.15, "medium": 0.35, "heavy": 0.60}
OP_PROBS = {"truncate": 0.4, "swap_benign": 0.4, "drop": 0.2}
ACK_TOKENS = ["k", "ok", "yep", "lol", "idk", "cool", "maybe", "sure"]
BENIGN_BANK_SIZE = 20_000
MIN_KEEP_FRAC = 0.25
MIN_KEEP_ABS = 3

# ── Shared PAN 2012 I/O and split (identical to exp_trajectory_lift.py) ────────
sys.path.insert(0, str(SCRIPT_DIR))
from exp_trajectory_lift import (  # noqa: E402
    load_predators, parse_pan12, stratified_split, operating_point_at_fpr,
)


# ── Perturbation ────────────────────────────────────────────────────────────────
def perturb_conversation(msgs: list, strength: float, rng: np.random.Generator,
                         benign_bank: list) -> tuple:
    """
    Apply discourse-noise perturbation to one conversation's messages.
    Returns (perturbed_messages, op_counts) where op_counts tracks what was
    done for the sanity checks. Author IDs are preserved on surviving
    messages. No text is printed.
    """
    n = len(msgs)
    ops = {"kept": 0, "truncated": 0, "swapped_benign": 0, "dropped": 0,
           "adjacent_transpositions": 0, "drop_guard_hits": 0}
    if n == 0 or strength <= 0.0:
        ops["kept"] = n
        return list(msgs), ops

    min_keep = max(MIN_KEEP_ABS, int(np.ceil(MIN_KEEP_FRAC * n)))
    op_names = list(OP_PROBS.keys())
    op_p = np.array([OP_PROBS[k] for k in op_names])

    out = []
    n_surviving = n
    for author, text in msgs:
        if rng.random() >= strength:
            out.append((author, text))
            ops["kept"] += 1
            continue
        op = op_names[rng.choice(len(op_names), p=op_p)]
        if op == "drop" and (n_surviving - 1) < min_keep:
            op = "truncate"          # guard: never hollow out a conversation
            ops["drop_guard_hits"] += 1
        if op == "drop":
            n_surviving -= 1
            ops["dropped"] += 1
            continue
        if op == "truncate":
            words = text.split()
            if len(words) > 3 and rng.random() < 0.5:
                new_text = " ".join(words[:int(rng.integers(1, 4))])
            else:
                new_text = ACK_TOKENS[int(rng.integers(0, len(ACK_TOKENS)))]
            out.append((author, new_text))
            ops["truncated"] += 1
        else:  # swap_benign
            out.append((author, benign_bank[int(rng.integers(0, len(benign_bank)))]))
            ops["swapped_benign"] += 1

    # Order jitter: strength-proportional adjacent transpositions
    m = len(out)
    if m >= 2:
        k = int(round(strength * (m - 1) * 0.5))
        for _ in range(k):
            i = int(rng.integers(0, m - 1))
            out[i], out[i + 1] = out[i + 1], out[i]
        ops["adjacent_transpositions"] = k
    return out, ops


def token_set(msgs: list) -> set:
    toks = set()
    for _, text in msgs:
        toks.update(text.lower().split())
    return toks


def jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / max(len(a | b), 1)


# ── Scoring helpers ─────────────────────────────────────────────────────────────
def score_baseline(msgs, vectorizer, svc) -> float:
    texts = [t if t else " " for _, t in msgs]
    if not texts:
        return 0.0
    return float(svc.decision_function(vectorizer.transform(texts)).mean())


def conv_to_weighted_vec(msgs, vectorizer):
    L = len(msgs)
    texts = [t if t else " " for _, t in msgs]
    if not texts:
        return None
    X = vectorizer.transform(texts)
    weights = np.array([1.0 + 0.5 * (i / max(L - 1, 1)) for i in range(L)])
    weighted = X.multiply(weights[:, np.newaxis])
    return np.asarray(weighted.sum(axis=0)) / weights.sum()


def score_sequence(msgs, vectorizer, lr) -> float:
    vec = conv_to_weighted_vec(msgs, vectorizer)
    if vec is None:
        return 0.0
    return float(lr.decision_function(vec.reshape(1, -1))[0])


def metrics_at_threshold(y, scores, thr) -> dict:
    preds = (scores >= thr).astype(int)
    tp = int(((preds == 1) & (y == 1)).sum())
    fp = int(((preds == 1) & (y == 0)).sum())
    fn = int(((preds == 0) & (y == 1)).sum())
    tn = int(((preds == 0) & (y == 0)).sum())
    recall = tp / max(tp + fn, 1)
    precision = tp / max(tp + fp, 1)
    f1 = 2 * precision * recall / max(precision + recall, 1e-9)
    return {
        "auc": float(roc_auc_score(y, scores)),
        "recall": float(recall),
        "precision": float(precision),
        "f1": float(f1),
        "fpr": float(fp / max(fp + tn, 1)),
        "accuracy": float((tp + tn) / max(len(y), 1)),
    }


def bootstrap_auc_ci(y, scores, n_resamples=N_BOOTSTRAP, seed=SEED):
    rng = np.random.default_rng(seed)
    n = len(y)
    aucs = []
    for _ in range(n_resamples):
        idx = rng.integers(0, n, size=n)
        if y[idx].sum() == 0 or y[idx].sum() == n:
            continue
        aucs.append(roc_auc_score(y[idx], scores[idx]))
    return [float(np.percentile(aucs, 2.5)), float(np.percentile(aucs, 97.5))]


def sha256_ids(convs) -> str:
    h = hashlib.sha256()
    for cid in sorted(c[0] for c in convs):
        h.update(cid.encode())
    return h.hexdigest()


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

    # ── Parse, split, train (identical setup to exp_trajectory_lift.py) ────────
    print("Parsing PAN 2012 XML …")
    predators = load_predators(DATA_PRED)
    conversations = parse_pan12(DATA_XML, predators)
    train, test = stratified_split(conversations)
    y_test = np.array([label for _, label, _ in test], dtype=int)
    pos_idx = np.where(y_test == 1)[0]
    neg_idx = np.where(y_test == 0)[0]
    print(f"  train={len(train)}  test={len(test)} "
          f"(pos={len(pos_idx)}, neg={len(neg_idx)})")

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

    # Benign message bank for the swap op: training-split benign messages only
    # (4-25 words), so perturbation content cannot leak test information.
    bank_rng = np.random.default_rng(SEED)
    benign_candidates = [txt for _, label, msgs in train if label == 0
                         for _, txt in msgs if 4 <= len(txt.split()) <= 25]
    bank_pick = bank_rng.choice(len(benign_candidates),
                                size=min(BENIGN_BANK_SIZE, len(benign_candidates)),
                                replace=False)
    benign_bank = [benign_candidates[i] for i in bank_pick]
    print(f"  Benign swap bank: {len(benign_bank)} training-split benign messages")

    # ── Clean scores (strength 0) and fixed thresholds ─────────────────────────
    print("Scoring clean test set (both models) …")
    base_clean = np.array([score_baseline(m, vectorizer, svc) for _, _, m in test])
    seq_clean = np.array([score_sequence(m, vectorizer, lr) for _, _, m in test])
    base_thr, *_ = operating_point_at_fpr(y_test, base_clean, FPR_TARGET)
    seq_thr, *_ = operating_point_at_fpr(y_test, seq_clean, FPR_TARGET)
    print(f"  Thresholds calibrated on clean test at FPR<={FPR_TARGET} and held fixed.")

    base_neg_scores = base_clean[neg_idx]      # negatives stay clean throughout
    seq_neg_scores = seq_clean[neg_idx]
    test_pos = [test[i] for i in pos_idx]

    # ── Sweep ───────────────────────────────────────────────────────────────────
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

            # Sanity metrics for the first seed of each strength
            if ps in (None, PERTURBATION_SEEDS[0]):
                jac = [jaccard(orig_token_sets[i], token_set(pert_pos[i]))
                       for i in range(len(pert_pos))]
                order_changed = 0
                for i, (_, _, orig_msgs) in enumerate(test_pos):
                    surviving = [t for _, t in pert_pos[i]]
                    orig_texts = [t for _, t in orig_msgs]
                    # order considered changed if the surviving sequence is not a
                    # subsequence of the original sequence
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
                    "labels_unchanged": True,   # y_test held fixed by construction
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

    # ── Verdict on the target claim ─────────────────────────────────────────────
    # "Degrades more gracefully" requires the sequence model to retain more of
    # its clean AUC than the baseline at >= 2 non-zero strengths (mean over seeds).
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
    claim_supported = n_graceful >= 2
    verdict = {
        "claim": "sequence model degrades more gracefully than per-message "
                 "baseline under discourse perturbation",
        "criterion": "sequence AUC drop < baseline AUC drop (mean over seeds) "
                     "at >= 2 of 3 non-zero strengths",
        "per_strength": verdict_rows,
        "n_strengths_where_sequence_degrades_less": n_graceful,
        "supported": bool(claim_supported),
        "scope_caveat": "Within this discourse-noise family only; perturbation "
                        "families are limited and not exhaustive.",
    }

    output = {
        "experiment": "perturbation_sweep",
        "dataset": "PAN 2012 SPI training XML, 80/20 stratified "
                   "conversation-level split (same as exp_trajectory_lift.py)",
        "split_type": "stratified_conversation_level_80_20",
        "split_seed": SEED,
        "perturbation_seeds": PERTURBATION_SEEDS,
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
            "The sequence model is position-weighted averaging, not a true "
            "sequence encoder; its order sensitivity is weak by construction.",
            "Perturbation family is limited (truncate/benign-swap/drop/adjacent "
            "jitter); no paraphrase or feature-aware evasion is included.",
            "FPR is constant across strengths because negatives are unchanged "
            "and thresholds are fixed; degradation shows up in recall/AUC.",
            "Results are on the training-XML 80/20 conversation-level split; "
            "PAN 2012 validates 2012 human grooming, not 2026 agentic automation.",
        ],
        "figures": [
            str((OUT / "perturbation_sweep.pdf").relative_to(ROOT)),
            str((OUT / "perturbation_sweep.png").relative_to(ROOT)),
        ],
    }
    with open(OUT / "perturbation_sweep.json", "w") as fh:
        json.dump(output, fh, indent=2)

    sanity = {
        "experiment": "perturbation_sanity_checks",
        "source": "exp_perturbation_sweep.py (first seed of each strength)",
        "split_hash_sha256": {
            "train_conversation_ids": sha256_ids(train),
            "test_conversation_ids": sha256_ids(test),
            "note": "Perturbation is applied after the split; these hashes are "
                    "computed once and the split is identical for every "
                    "condition by construction.",
        },
        "labels": {
            "unchanged": True,
            "note": "y_test is held fixed; perturbation never adds/removes "
                    "conversations (drop guard keeps >= max(3, 25%) messages). "
                    "Ground-truth labels refer to the original conversations.",
            "label_balance": {"positives": int(len(pos_idx)),
                              "negatives": int(len(neg_idx))},
        },
        "metadata_fields": {
            "changed": False,
            "note": "Author IDs are preserved on surviving messages; the "
                    "pipeline carries no other metadata/telemetry fields.",
        },
        "text_surface": {
            "changed_for_nonzero_strengths": True,
            "how_and_why": "truncate (cadence/brevity noise), benign-swap "
                           "(retrieval-swap of training-split benign messages "
                           "to dilute content signal), drop (message removal), "
                           "adjacent transpositions (order jitter). Applied to "
                           "test positives only, to model an adaptive adversary "
                           "perturbing their own conversations.",
        },
        "per_condition": sanity_conditions,
    }
    with open(OUT / "perturbation_sanity_checks.json", "w") as fh:
        json.dump(sanity, fh, indent=2)

    # ── Figure ──────────────────────────────────────────────────────────────────
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
    fig.suptitle("Discourse-noise perturbation sweep — PAN 2012 "
                 "(positives perturbed, negatives clean; "
                 f"{len(PERTURBATION_SEEDS)} seeds)", fontsize=9.5)
    fig.tight_layout()
    fig.savefig(OUT / "perturbation_sweep.pdf", bbox_inches="tight")
    fig.savefig(OUT / "perturbation_sweep.png", dpi=150, bbox_inches="tight")
    plt.close(fig)

    print("\n=== Perturbation sweep verdict ===")
    for r in verdict_rows:
        print(f"  {r['strength_name']:6s}: baseline AUC drop {r['baseline_auc_drop']:+.3f}"
              f"  sequence AUC drop {r['sequence_auc_drop']:+.3f}"
              f"  -> sequence degrades less: {r['sequence_degrades_less']}")
    print(f"  Claim supported (>=2/3 strengths): {claim_supported}")
    print(f"\nResults: {OUT / 'perturbation_sweep.json'}")
    print(f"Sanity:  {OUT / 'perturbation_sanity_checks.json'}")


if __name__ == "__main__":
    main()
