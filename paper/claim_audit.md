# Claim audit — v9 empirical paper draft

> **Scope note (2026-07-07):** the USENIX-oriented source
> (`paper/usenix/adversarial_intent_telemetry_usenix.tex`) was produced by
> compressing the v9 draft with **no changes to any empirical claim or
> number**; this audit therefore covers both sources. Rows 1–30 below map
> claims to JSON evidence for both.

Audit of every major empirical claim in
`Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.tex` (draft v9.0, the
revised empirical paper) against the committed result JSONs. Performed
2026-07-06. All JSON paths are relative to `experiments/results/` unless
noted. "Qualified?" records whether the prose attaches the correct evidence
status and scope limits.

Verification route: `python3 scripts/check_claims.py` (26/26 pass against the
README, which carries the same headline numbers) plus direct field inspection
for the paper-only numbers listed here. The paper's four result tables are
machine-generated from the same JSONs by `scripts/build_paper_tables.py`.

| # | Claim (summary) | Paper section | Source JSON | Field(s) | Value in JSON | Status | Qualified? |
|---|---|---|---|---|---|---|---|
| 1 | Per-message clean AUC 0.986 | Abstract, §1, §2, RQ1 (Tab. clean) | `trajectory_lift.json` | `baseline.auc_roc` | 0.98642 | real-data | Yes — split named (stratified conversation-level), robustness explicitly excluded |
| 2 | Per-message recall 0.948 at FPR ≤ 0.05 | Abstract ("0.95"), RQ1 | `trajectory_lift.json` | `baseline.recall_at_fpr_target` (`actual_fpr` 0.0421) | 0.94802 | real-data | Yes |
| 3 | Per-message precision 0.412 at that point | RQ1, §8.2 ("0.41") | `trajectory_lift.json` | `baseline.precision_at_fpr_target` | 0.41227 | real-data | Yes — used to argue most alerts are FPs |
| 4 | Sequence clean AUC 0.977 | Abstract, RQ3 | `trajectory_lift.json` | `sequence_model.auc_roc` | 0.97726 | real-data | Yes |
| 5 | Sequence recall 0.933; shuffle 0.923 | RQ3 | `trajectory_lift.json` | `sequence_model.recall_at_fpr_target`; `evasion_simulation.sequence_recall_original/_shuffled` | 0.93317 / 0.92327 | real-data | Yes — framed as order-sensitivity asymmetry, not lift |
| 6 | Clean F1 lift −0.023, 95% CI [−0.042, −0.002] | Abstract, §1, §2, RQ3 | `trajectory_lift.json` | `key_metric.value`, `key_metric.bootstrap_95ci` | −0.02267, [−0.04224, −0.00188] | negative / inconclusive | Yes — scope limited to this representation |
| 7 | MinHash (16,16): recall 0.018 at FPR 0.0013 | Abstract, §1, §2, RQ2 (Tab. frontier) | `m3_frontier.json` | `operating_points[b=16,r=16].federated_recall/.federated_fpr`; `split_type` | 0.01826 / 0.00131; `author_disjoint` | negative result (real data) | Yes — headline negative finding |
| 8 | MinHash (128,2): recall 0.92 only at FPR 0.99 | Abstract, RQ2 | `m3_frontier.json` | `operating_points[b=128,r=2].federated_recall/.federated_fpr` | 0.92237 / 0.98797 | negative result (real data) | Yes — prose says 0.988 in RQ2, 0.99 in abstract (consistent rounding) |
| 9 | Pool/test sizes: 1,720 signatures; 13,202 test convs, 219 pos | §6.2, RQ2 | `m3_frontier.json` | `n_valid_train_pos_sigs`, `n_test`, `n_test_pos`, `n_predator_authors_train/test` | 1720 / 13202 / 219 / 113/29 | real-data (descriptive) | Yes |
| 10 | Sweep baseline AUC 0.986→0.971→0.949→0.912 | Abstract, RQ4 (Tab. sweep) | `perturbation_sweep.json` | `conditions[*].baseline.auc.mean` | 0.98642 / 0.97063 / 0.94898 / 0.91154 | perturbation-result (real data) | Yes — one family, conversation-level split both flagged |
| 11 | Sweep sequence AUC 0.977→0.968→0.955→0.940 | Abstract, RQ4 | `perturbation_sweep.json` | `conditions[*].sequence.auc.mean` | 0.97726 / 0.96762 / 0.95540 / 0.94040 | perturbation-result | Yes |
| 12 | Sequence AUC drop smaller at all 3 non-zero strengths; heavy 0.037 vs 0.075 | Abstract, §1, §2, RQ4 | `perturbation_sweep.json` | `verdict.per_strength[*].baseline_auc_drop/.sequence_auc_drop`, `verdict.supported` | heavy: 0.07488 vs 0.03686; `supported: true` | perturbation-result | Yes — "degrades more gracefully" used only with the family caveat |
| 13 | 5 seeds per non-zero strength | RQ4, §6.3 | `perturbation_sweep.json` | `perturbation_seeds` | [0,1,2,3,4] | perturbation-result (design) | Yes |
| 14 | FP substrate: classifier 0.030 vs control 0.055 | Abstract, §2, RQ5 (Tab. fps) | `fp_substrate.json` | `summary.classifier_fpr05.structural_FPR_mean/.control_FPR_mean`; `split_type`; `sampling_seeds`; `n_substrate` | 0.0300 / 0.05533; `author_disjoint_80_20`; [0,1,2]; 500 | real-data (proxy substrate) | Yes — proxy status and non-clearing of deployment risk both stated |
| 15 | MinHash flags almost nothing in either set (0 vs 1 convs total) | RQ5 | `fp_substrate.json` | `per_seed[*].minhash_16_16.n_structural_fp/.n_control_fp` | 0+0+0 / 1+0+0 | real-data (proxy substrate) | Yes |
| 16 | Byzantine β* = 0.5; stealth β* = 0.4 | §2, RQ6 | `m8_byzantine.json`; `m8_sprt.json` | `key_metric.value`; `summary.stealth_operational_beta_star` | 0.5; 0.4 | simulation | Yes — "simulation only", parameters-scoped |
| 17 | SPRT 2.27× faster than Hoeffding; SPRT false-isolation ≤ 0.044; Hoeffding comparator weak (~0.996 false isolation) | §2, RQ6, §8.2 | `m8_sprt.json` | `summary.sprt_vs_hoeffding_speedup_factor`, `summary.sprt_false_isolation_rate_max`, `methodology_notes.hoeffding_baseline_false_isolation` | 2.2739; 0.04449; note present | simulation (weak comparator) | Yes — paper explicitly says the false-isolation gap must not be quoted as a finding |
| 18 | F3: cooperation +0.184; PD defection 1.0→0.57 | §2, RQ6 | `f3_reciprocity.json` | `key_metric.value`; `baseline.per_game["Prisoner's Dilemma"]`; `combined_a_b_c_tau_rho_delta_1.per_game["Prisoner's Dilemma"].defection_rate` | 0.18409; 1.0; 0.57187 | analytical | Yes — "mechanism design on matrices; not LLM behavior, not deployment" |
| 19 | Synthetic S-curve: empirical within 0.05 of closed form; recall 0.085 / FPR 0.0002 at (16,16) | §5.6 (Tab. scurve) | `validation/synthetic/results/results.json` | `operating_points[b=16,r=16].recall/.FPR` (also (8,32): 0.0048/0.0; (32,8): 0.515/0.0252) | 0.0854 / 0.0002 | synthetic (sanity check) | Yes — explicitly "no bearing on real-data utility"; real frontier stated to supersede |
| 20 | Single-point discourse noise AUC 0.92→0.79 | RQ4 (context) | `realism_delta_metrics.json` | `pre_auc`, `post_auc` | 0.92111, 0.78667 | perturbation-result (single point) | Yes — cited as the single-point observation the sweep supersedes |
| 21 | NCMEC-constrained set: baseline AUC 0.13, sequence 0.57 | RQ4 (context) | `detection_ncmec.json` | `metrics["AUC (Baseline)"], metrics["AUC (Sequence)"]` | 0.13286, 0.56964 | perturbation-result (single point, Tier-2 data) | Yes — flagged as single point without seed variance; NCMEC figures described as sampling priors only (§3, §6.1) |
| 22 | PAN corpus size 66,927 convs, ~3% positive | §6.1 | `m3_frontier.json` | `n_total_conversations` (66927); positives 1797+219=2016 → 3.0% | 66927; ~3% | real-data (descriptive) | Yes — "roughly 3%" (was fixed from an earlier over-specific phrasing) |
| 23 | Substrate pools 3,979 / 9,004 | §6.3 | `fp_substrate.json` | `substrate_pool_size`, `control_pool_size` | 3979, 9004 | real-data (descriptive) | Yes |
| 24 | A2 agentic automation as operative adversary | §3, §4 | (none — reporting-motivated) | n/a | n/a | design-context / motivation | Yes — "design target, motivated by reporting, not validated in this study"; limitation (1) repeats it |
| 25 | Latency/throughput targets (sub-50 ms etc.) | §9 (Ethics/non-claims) | (none — design doc) | n/a | n/a | design-context | Yes — explicitly "no implementation was built or measured here" |

Rows 26–30 added 2026-07-07 (RQ4 stress-test pass):

| # | Claim (summary) | Paper section | Source JSON | Field(s) | Value in JSON | Status | Qualified? |
|---|---|---|---|---|---|---|---|
| 26 | Author-disjoint replication: sequence degrades less at all 3 strengths; heavy drop 0.029 vs 0.058 | Abstract, §1, §2, RQ4 (Tab. sweep-adj) | `perturbation_sweep_author_disjoint.json` | `verdict.per_strength[*]`, `verdict.supported` | drops 0.0064/0.0125/0.0293 vs 0.0120/0.0277/0.0583; `supported: true` | perturbation-result (real data, author-disjoint) | Yes |
| 27 | Sequence advantage statistically resolved vs every per-message comparison | RQ4 (Tab. paired) | `perturbation_paired_tests.json` | `comparisons.{per_message_mean,per_message_max,per_message_top5,conv_concat}.*.ci95/ci_excludes_zero` | all CIs < 0, exclude zero | perturbation-result (paired bootstrap) | Yes |
| 28 | Order-invariant conversation-mean control at least as robust as sequence model; attribution = aggregation, not order | Abstract, §1, §2, RQ4, §8.1 | `perturbation_paired_tests.json`; `perturbation_model_controls.json` | `comparisons.conv_mean.*` (favors=comparator, all strengths); `degradation[*].models.conv_mean/.sequence` | conv_mean drops 0.0048/0.0103/0.0260 vs sequence 0.0064/0.0125/0.0293; CIs exclude zero favoring comparator | negative result for trajectory attribution (real data) | Yes — headline attribution correction |
| 29 | Shuffled-order control tracks the sequence model (model barely uses order) | RQ4, Limitations (4) | `perturbation_model_controls.json` | `degradation[*].models.sequence_shuffled` | drops 0.0061/0.0121/0.0297 ≈ sequence | negative result (order-usage control) | Yes |
| 30 | Second family (surface_rewrite_rule_based) leaves all models essentially unaffected (max mean drop < 0.002) | Abstract (limits), RQ4, Limitations (2) | `perturbation_second_family.json` | `degradation[*].models.*.auc_drop` | all |drop| ≤ 0.0018 | null / uninformative for the comparison | Yes — explicitly stated as uninformative |

Also fixed in this pass: `ci_excludes_zero` flag (see below); `check_claims.py`
extended to 31 checks including the author-disjoint drops, the attribution
backing, and the CI-flag consistency.

## Findings

- **No unsupported or overprecise claims found.** Every number in the paper
  traces to a JSON field; rounding is at 2–4 significant digits and never
  tighter than the source.
- One earlier overprecision (corpus positives phrased as a split-specific
  count) was fixed in the v9 draft before this audit
  ("roughly 3% involving a labeled predator author").
- Claims 20–21 are single-point perturbation observations; the paper
  correctly subordinates them to the sweep (claim 10–12) rather than
  presenting them as calibrated results.
- ~~The `trajectory_lift.json` field `key_metric.ci_excludes_zero` is `false`
  even though both CI endpoints are negative.~~ **Fixed 2026-07-06**: the flag
  logic in `exp_trajectory_lift.py` only tested the positive direction
  (`ci_lo > 0`); it now tests both directions, the JSON was regenerated
  (all metric values unchanged; flag now `true`, status still
  `inconclusive` since the lift is negative), and `scripts/check_claims.py`
  verifies flag/CI consistency.
