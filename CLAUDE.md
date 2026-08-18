# CLAUDE.md — Adversarial Intent Telemetry

Persistent context for Claude Code sessions on this repository. Read fully before
editing any file. Update the **Repository State** table whenever a file is added,
removed, or renamed.

---

## 1. Project Identity

**What this is**: A public empirical-research repository. It evaluates whether a
cross-provider behavioral-signature detection scheme survives real adversarial data
and adaptive perturbation. The scheme — a banded-MinHash signature primitive plus a
trajectory-level sequence model — was originally specified as a deployable protocol
in the design paper. **The paper is the design under test; the repository reports
what the primitives actually do when run.**

**Framing rule (do not drift from this)**: This is an honest empirical study with a
mixed result, not a protocol announcement. The headline is the *decomposition* of
where behavioral detection holds (per-message on clean PAN 2012) and where it breaks
(the signature primitive on real text; the per-message detector under perturbation).
Negative and inconclusive results are reported as such. Never restate the design
paper's `demonstrated`-level protocol claims as if the repository validated them.

**Design paper**: `Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.pdf` (included
as the design under test).
**Author**: Fahrawn Gill, Advisor, AI Governance & Cross-Platform Safety, ACCO.

**What the repository must communicate, in order of importance:**
1. The falsifiable question and the mixed result (results table in README).
2. Which claims are real / simulated / analytical / inconclusive.
3. The integrity infrastructure (truth ledger, validity-boundary statement).
4. What is actually in the repository right now.
5. The design under test (the paper), framed as such.

---

## 2. Target Audience

Primary: empirical AI-safety and adversarial-ML researchers (the kind who clone the
repo and re-run the numbers). Secondary: T&S / detection engineers, AI-governance
staff, technically sophisticated hiring managers.

These readers will clone the repo if the README is compelling, and the repo must
then hold up. They trust epistemic modesty over confident claims, and they will
notice instantly if the README describes results the result files do not support.

---

## 3. Repository State

**This table is the source of truth for what the README may describe as existing.**
Update it on every add/remove/rename.

| Path | Status | Notes |
|---|---|---|
| `README.md` | exists | Empirical-study framing (B). No merge-conflict markers. |
| `CLAUDE.md` | exists | This file. |
| `AGENTS.md` | exists | Session/agent instructions. |
| `LICENSE.md` | exists | AGPL v3. |
| `Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.pdf` | exists | Design under test. |
| `spec/manifest-schema.json` | exists | Feature manifest schema (Appendix A). |
| `examples/trajectory.json` | exists | Synthetic adversarial trajectory example. |
| `tools/manifest_gen.py` | exists | Rule-based manifest extractor (AI-jailbreak patterns; low transfer to PAN 2012). |
| `tools/inject_discourse_noise.py` | exists | Perturbation: retrieval-swap, reciprocity-asymmetry. |
| `tools/audit_human_vs_generated.py`, `tools/audit_structural_diversity.py` | exists | Synthetic-vs-real audits. |
| `tools/pan12_empirical_grounding.py` | exists | PAN 2012 grounding stats. |
| `tools/requirements.txt` | exists | Tooling deps. |
| `validation/synthetic/s_curve.py` | exists | **Illustrative** S-curve on synthetic Beta pairs. Not real-data performance. |
| `validation/synthetic/results/` | exists | s_curve.png, results.json. |
| `experiments/exp_m3_author_split.py` | exists | Author-disjoint PAN split. |
| `experiments/exp_m3_frontier.py` | exists | Operating-point frontier on real PAN 2012. |
| `experiments/exp_m3_federation_lift.py` | exists | Federation lift sweep. |
| `experiments/exp_trajectory_lift.py` | exists | Per-message vs sequence + evasion test (lift negative). |
| `experiments/exp_m8_byzantine.py`, `exp_m8_sprt.py` | exists | Byzantine / SPRT simulation. |
| `experiments/exp_f3_reciprocity.py` | exists | Analytical payoff-perturbation on GT-HarmBench. |
| `experiments/exp_perturbation_sweep.py` | exists | Dose-response perturbation sweep (none/light/medium/heavy, 5 seeds); also writes `perturbation_sanity_checks.json`. |
| `experiments/exp_fp_substrate.py` | exists | FP substrate: keyword-matched benign vs random benign controls; structural FPR not elevated (finding). |
| `experiments/exp_perturbation_sweep_author_disjoint.py` | exists | Author-disjoint replication of the discourse-noise sweep (RQ4 stricter split). |
| `experiments/exp_perturbation_model_controls.py` | exists | Aggregation/order controls (7 models incl. order-invariant twins + shuffled control) + paired bootstrap; writes `perturbation_paired_tests.json`. |
| `experiments/exp_perturbation_second_family.py` | exists | Second perturbation family (`surface_rewrite_rule_based`) under the same model-control framework. |
| `tools/inject_surface_rewrite_noise.py` | exists | Rule-based surface-rewrite/segmentation perturbation family (chat-register substitutions, casing/punct jitter, split/merge). |
| `experiments/exp_annotate_pan_manifest.py` | exists | PAN manifest annotation (low field population, reported). |
| `experiments/exp_xplat_continuity.py` | exists | Cross-platform continuity sweep. |
| `experiments/exp_generate_*.py`, `regen_*.py`, `fill_missing_*.py`, `final_push_generation.py` | exists | Tier 0/2 trajectory generation utilities. |
| `experiments/results/*.json,*.csv,*.txt` | exists | All result artifacts incl. `truth_ledger.json`, `validity_boundary_statement.txt`. |
| `experiments/results/*.png,*.pdf` | exists | Figures. |
| `requirements.txt` | exists | Root install target for all public (non-restricted-data) experiments; README installs from this. |
| `scripts/reproduce_public.sh` | exists | Runs experiments that don't require PAN 2012; skips GT-HarmBench gracefully if its gated CSV is absent. |
| `scripts/check_claims.py` | exists | Verifies README headline numbers against `experiments/results/*.json`; fails on drift. |
| `scripts/build_paper_tables.py` | exists | Generates `paper/tables/*.tex` result tables from result JSONs. |
| `Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.tex` | exists | **Revised (2026-07-06)** into the empirical-study paper ("Adversarial Intent Telemetry: An Empirical Study…", draft v9.0). Compiles to `paper/build/` (gitignored); the original protocol-spec source is preserved at `..._v8.1_backup.tex`. |
| `Decentralized_Telemetry_Adversarial_AI_Intent_v8.1_backup.tex` | exists | Verbatim backup of the original v8.1 protocol-spec LaTeX source. |
| `paper/tables/*.tex` | exists | Machine-generated result tables (clean detection, MinHash frontier, perturbation sweep, FP substrate); regenerate via `scripts/build_paper_tables.py`, do not hand-edit. |
| `paper/claim_audit.md` | exists | Per-claim audit of the v9 paper against result JSONs (claim → section → JSON field → status → qualification). |
| `paper/bibliography_audit.md` | exists | Per-reference audit: formalize / replace-with-primary / remove? / verify dispositions; no citations invented. |
| `paper/usenix_migration_plan.md` | exists | USENIX template conversion plan; status banner records the executed conversion (2026-07-07). |
| `paper/usenix/adversarial_intent_telemetry_usenix.tex` | exists | USENIX-oriented submission source (9 two-column pages, BibTeX, fallback geometry preamble + `\IfFileExists` hook for the official `usenix2019_v3.sty`, which is NOT in the repo). Compile from repo root with `-output-directory=paper/build -jobname=usenix_draft`. |
| `paper/references.bib` | exists | BibTeX transcription of the v9 reference list; TODO(verify)/TODO(replace) notes carried in-entry; no invented identifiers or years. |
| `paper/length_reduction_plan.md` | exists | What was cut v9→USENIX and where each item survives. |
| `paper/anonymization_checklist.md` | exists | Switch-gated vs manual anonymization steps; self-identifying-text inventory. |
| `paper/artifact_appendix.md` | exists | Markdown master of the artifact-evaluation appendix (LaTeX twin = Appendix A of the USENIX source). |
| `docs/data_audit.md` | exists | Audit of tracked `data/` files for raw PAN 2012 text; documents one confirmed finding and its remediation. |
| `data/pan12/` | gitignored | Raw PAN 2012 corpus — NOT redistributed. `data/pan12/README.md` (+ `train/README.md`, `test/readme.md`) carry real provenance notes. |
| `data/gt_harmbench/` | gitignored (CSV) | GT-HarmBench is a gated HuggingFace dataset — NOT redistributed. `data/gt_harmbench/README.md` carries real provenance notes. |
| `data/pan_annotated/pan_manifests_v2.jsonl`, `data/pan_annotated/adapted_trajectories.jsonl`, `data/pan_annotated/regenerated_trajectories.jsonl`, `data/agentic_ncmec/pan_ncmec_trajectories.jsonl` | tracked | Structural-feature or text-audited synthetic files; see `docs/data_audit.md` for the per-file audit. |
| `data/pan_annotated/regenerated_trajectories_noisy.jsonl` | **untracked (removed)** | Confirmed to contain verbatim PAN 2012 text via `tools/inject_discourse_noise.py`'s retrieval-swap; `git rm --cached` and gitignored. Posture recalibrated 2026-07-06: PAN 2012 is public/open research data, so no history rewrite is planned (see §4 and `docs/data_audit.md`). |

**Hard rule**: The README must never describe, link to, or give commands for a path
not marked `exists` here. The README must never describe a result the corresponding
result file does not support.

---

## 4. Known hygiene items

Resolved in the repository-hardening pass:
- `.DS_Store` and `.claude/worktrees/` were checked and were never tracked in
  Git; both remain covered by `.gitignore`.
- `data/.gitignore` now carries explicit `!exceptions` for every intentionally
  tracked derived file, so future re-generation of those files won't be
  silently dropped by the broad `*.json`/`*.csv` rules.
- `m8_byzantine.json` and `f3_reciprocity.json` stored absolute
  `/Users/fahrawngill/...` paths in their `figures` fields (an artifact of
  Python resolving `__file__` to an absolute path). Fixed at the source in
  `experiments/exp_m8_byzantine.py` and `experiments/exp_f3_reciprocity.py`
  (`.relative_to(ROOT)` before serializing) and both JSONs regenerated.
- `data/README.md`, `data/pan12/README.md` (+ `train/README.md`,
  `test/readme.md`), and `data/gt_harmbench/README.md` had only `placeholder`
  — replaced with real provenance, redistribution status, and safety
  language.
- `data/pan_annotated/regenerated_trajectories_noisy.jsonl` was found during
  the data audit to contain verbatim PAN 2012 text and was untracked; see
  `docs/data_audit.md`.

Still open:
- Git history contains `data/pan_annotated/regenerated_trajectories_noisy.jsonl`
  from commit `d868234` onward. Posture recalibration (2026-07-06): PAN 2012
  is public/open research data, so this is a provenance/consistency issue,
  not a confidentiality leak. The file is untracked going forward; **no
  history rewrite is planned** unless a PAN license violation is identified
  or the owner requests it. See `docs/data_audit.md`.
- Root-level `experiment.py`, `results.json`, `run_all_experiments.py`, and
  the `experiments2/` directory exist on disk but are not part of this
  table and are not referenced by the README. Leave them alone unless the
  user asks — do not delete without confirming they're not in-progress work.

---

## 5. Claim discipline (the Maturity language)

When describing any result, attach one of:
- **real** — measured on PAN 2012 / GT-HarmBench real data (author-disjoint where noted).
- **simulation** — Byzantine / SPRT results; validate a mechanism under stated params, not a deployment.
- **analytical** — F3 reciprocity; mechanism-design claim on game matrices, not LLM behavior.
- **synthetic** — Tier 0 and the s_curve harness; ablation / illustrative only.
- **negative / inconclusive** — e.g. trajectory F1 lift (CI below zero); state plainly.

Headline detection claims rest only on **real** Tier 1 results.
