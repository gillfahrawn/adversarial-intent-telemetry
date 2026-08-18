#!/usr/bin/env python3
"""
Claim-consistency checker.

Reads the headline numbers out of experiments/results/*.json and confirms each
one still appears, correctly rounded, in README.md. Fails with a clear message
naming the check, the JSON value, and the string it could not find if a number
in the README has drifted from the result file it is supposed to report.

This does not evaluate whether a claim is framed honestly (that is a human
editorial judgment governed by CLAUDE.md) — only whether the number in the
README still matches the number in the committed evidence.

Usage: python scripts/check_claims.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RESULTS = ROOT / "experiments" / "results"
README = ROOT / "README.md"


def load(name):
    with open(RESULTS / name) as fh:
        return json.load(fh)


def clean(text: str) -> str:
    """Strip markdown emphasis markers so '**0.986**' matches '0.986'."""
    return text.replace("**", "")


def check(readme_text: str, description: str, file: str, value: float, fmt: str, results: list):
    expected = fmt.format(value)
    ok = expected in readme_text
    results.append((ok, description, file, expected))
    return ok


def main() -> int:
    if not README.exists():
        print(f"ERROR: {README} not found.", file=sys.stderr)
        return 1

    readme_text = clean(README.read_text())
    results = []

    # -- Per-message classifier on clean PAN 2012 (conversation-level split) --
    traj = load("trajectory_lift.json")
    check(readme_text, "per-message AUC (trajectory_lift.json baseline.auc_roc)",
          "trajectory_lift.json", traj["baseline"]["auc_roc"], "{:.3f}", results)
    check(readme_text, "per-message recall @ FPR=0.05 (trajectory_lift.json baseline.recall_at_fpr_target)",
          "trajectory_lift.json", traj["baseline"]["recall_at_fpr_target"], "{:.2f}", results)

    # -- Sec. 6 clean trajectory F1 lift and 95% CI --
    lift = traj["key_metric"]["value"]
    ci_lo, ci_hi = traj["key_metric"]["bootstrap_95ci"]
    check(readme_text, "trajectory F1 lift (trajectory_lift.json key_metric.value)",
          "trajectory_lift.json", lift, "{:.3f}", results)
    check(readme_text, "trajectory F1 lift CI lower bound",
          "trajectory_lift.json", ci_lo, "{:.3f}", results)
    check(readme_text, "trajectory F1 lift CI upper bound",
          "trajectory_lift.json", ci_hi, "{:.3f}", results)

    # -- Internal consistency: the CI-excludes-zero flag must match the CI --
    ci_lo, ci_hi = traj["key_metric"]["bootstrap_95ci"]
    flag = traj["key_metric"]["ci_excludes_zero"]
    flag_ok = flag == (ci_lo > 0.0 or ci_hi < 0.0)
    results.append((flag_ok, "trajectory_lift.json ci_excludes_zero flag is "
                             "consistent with its own bootstrap_95ci",
                    "trajectory_lift.json",
                    f"flag={flag}, ci=[{ci_lo:.3f}, {ci_hi:.3f}]"))

    # -- MinHash operating-point frontier on PAN 2012, author-disjoint split --
    frontier = load("m3_frontier.json")
    points = {(p["b"], p["r"]): p for p in frontier["operating_points"]}
    p16 = points[(16, 16)]
    check(readme_text, "MinHash recall at recommended (b=16, r=16)",
          "m3_frontier.json", p16["federated_recall"], "{:.3f}", results)
    check(readme_text, "MinHash FPR at recommended (b=16, r=16)",
          "m3_frontier.json", p16["federated_fpr"], "{:.4f}", results)
    p128 = points[(128, 2)]
    check(readme_text, "MinHash high-recall operating point recall (b=128, r=2)",
          "m3_frontier.json", p128["federated_recall"], "{:.2f}", results)
    check(readme_text, "MinHash high-recall operating point FPR (b=128, r=2)",
          "m3_frontier.json", p128["federated_fpr"], "{:.2f}", results)

    # -- Perturbation: discourse-noise AUC drop --
    realism = load("realism_delta_metrics.json")
    check(readme_text, "discourse-noise pre-perturbation AUC",
          "realism_delta_metrics.json", realism["pre_auc"], "{:.2f}", results)
    check(readme_text, "discourse-noise post-perturbation AUC",
          "realism_delta_metrics.json", realism["post_auc"], "{:.2f}", results)

    # -- Perturbation: NCMEC-constrained realism set --
    ncmec = load("detection_ncmec.json")
    check(readme_text, "NCMEC-set per-message AUC (below random)",
          "detection_ncmec.json", ncmec["metrics"]["AUC (Baseline)"], "{:.2f}", results)
    check(readme_text, "NCMEC-set sequence-model AUC",
          "detection_ncmec.json", ncmec["metrics"]["AUC (Sequence)"], "{:.2f}", results)

    # -- Byzantine tolerance (simulation) --
    byz = load("m8_byzantine.json")
    check(readme_text, "Byzantine empirical beta*",
          "m8_byzantine.json", byz["key_metric"]["value"], "{:.1f}", results)

    # -- SPRT vs. Hoeffding isolation speed + stealth beta* (simulation) --
    sprt = load("m8_sprt.json")
    check(readme_text, "SPRT vs. Hoeffding speedup factor",
          "m8_sprt.json", sprt["summary"]["sprt_vs_hoeffding_speedup_factor"], "{:.2f}", results)
    check(readme_text, "stealth-adversary operational beta*",
          "m8_sprt.json", sprt["summary"]["stealth_operational_beta_star"], "{:.1f}", results)

    # -- Perturbation sweep (discourse-noise family, 5 seeds) --
    sweep = load("perturbation_sweep.json")
    cond = {c["strength_name"]: c for c in sweep["conditions"]}
    check(readme_text, "sweep clean baseline AUC (perturbation_sweep.json none.baseline.auc.mean)",
          "perturbation_sweep.json", cond["none"]["baseline"]["auc"]["mean"], "{:.3f}", results)
    check(readme_text, "sweep clean sequence AUC",
          "perturbation_sweep.json", cond["none"]["sequence"]["auc"]["mean"], "{:.3f}", results)
    check(readme_text, "sweep heavy baseline AUC (mean over seeds)",
          "perturbation_sweep.json", cond["heavy"]["baseline"]["auc"]["mean"], "{:.3f}", results)
    check(readme_text, "sweep heavy sequence AUC (mean over seeds)",
          "perturbation_sweep.json", cond["heavy"]["sequence"]["auc"]["mean"], "{:.3f}", results)
    n_graceful = sweep["verdict"]["n_strengths_where_sequence_degrades_less"]
    if "degrades more gracefully" in readme_text or "degrades less" in readme_text:
        ok = sweep["verdict"]["supported"]
        results.append((ok, "README 'degrades more gracefully' language is backed by "
                            "perturbation_sweep.json verdict.supported",
                        "perturbation_sweep.json", f"supported={ok}, "
                        f"{n_graceful}/3 strengths"))

    # -- Author-disjoint perturbation sweep replication --
    adj = load("perturbation_sweep_author_disjoint.json")
    adj_heavy = {r["strength_name"]: r for r in adj["verdict"]["per_strength"]}["heavy"]
    check(readme_text, "author-disjoint sweep heavy baseline AUC drop",
          "perturbation_sweep_author_disjoint.json",
          adj_heavy["baseline_auc_drop"], "{:.3f}", results)
    check(readme_text, "author-disjoint sweep heavy sequence AUC drop",
          "perturbation_sweep_author_disjoint.json",
          adj_heavy["sequence_auc_drop"], "{:.3f}", results)
    results.append((adj["verdict"]["supported"],
                    "author-disjoint sweep verdict.supported backs the README "
                    "replication claim", "perturbation_sweep_author_disjoint.json",
                    f"supported={adj['verdict']['supported']}"))

    # -- Aggregation/order-control attribution --
    if "order-invariant" in readme_text:
        paired = load("perturbation_paired_tests.json")
        cm = paired["comparisons"]["conv_mean"]
        ok = all(cm[s]["favors"] == "comparator" for s in ("light", "medium", "heavy"))
        results.append((ok, "README attribution ('order-invariant control at "
                            "least as robust') is backed by perturbation_paired_"
                            "tests.json conv_mean rows",
                        "perturbation_paired_tests.json",
                        f"conv_mean favors={[cm[s]['favors'] for s in ('light','medium','heavy')]}"))

    # -- FP substrate analysis --
    fps = load("fp_substrate.json")
    cls = fps["summary"]["classifier_fpr05"]
    check(readme_text, "FP substrate: classifier structural FPR (mean over seeds)",
          "fp_substrate.json", cls["structural_FPR_mean"], "{:.3f}", results)
    check(readme_text, "FP substrate: classifier control FPR (mean over seeds)",
          "fp_substrate.json", cls["control_FPR_mean"], "{:.3f}", results)

    # -- F3 reciprocity mechanism (analytical, GT-HarmBench) --
    f3 = load("f3_reciprocity.json")
    check(readme_text, "F3 overall cooperation improvement",
          "f3_reciprocity.json", f3["key_metric"]["value"], "{:.3f}", results)
    pd_baseline = f3["baseline"]["per_game"]["Prisoner's Dilemma"]
    pd_combined = f3["combined_a_b_c_tau_rho_delta_1"]["per_game"]["Prisoner's Dilemma"]["defection_rate"]
    check(readme_text, "F3 baseline Prisoner's Dilemma defection rate",
          "f3_reciprocity.json", pd_baseline, "{:.1f}", results)
    check(readme_text, "F3 combined-mechanism Prisoner's Dilemma defection rate",
          "f3_reciprocity.json", pd_combined, "{:.2f}", results)

    # -- Report --
    n_fail = sum(1 for ok, *_ in results if not ok)
    for ok, description, file, expected in results:
        status = "OK  " if ok else "FAIL"
        print(f"[{status}] {description}")
        if not ok:
            print(f"         expected to find {expected!r} (from {file}) in README.md — not found")

    print()
    if n_fail:
        print(f"{n_fail}/{len(results)} claim checks FAILED.")
        print("README.md numbers have drifted from the committed result JSON files,")
        print("or the formatting in this script no longer matches how the README")
        print("presents that number. Fix the README (or this script, if the")
        print("formatting assumption is stale) before treating the claims as current.")
        return 1

    print(f"All {len(results)} claim checks passed. README.md numbers match experiments/results/*.json.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
