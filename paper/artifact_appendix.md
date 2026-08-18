# Artifact appendix (markdown master)

Markdown master of the artifact appendix; the LaTeX version lives as
Appendix A of `paper/usenix/adversarial_intent_telemetry_usenix.tex`. Keep
the two in sync: this file is the editable source of record for artifact
evaluation (AE) submission forms.

## Artifact abstract

The artifact contains every experiment script, every result JSON cited by
the paper, the perturbation tools, machine-generated result tables and
their generator, claim-consistency checks, a truth ledger, a
validity-boundary statement, per-file data-provenance documentation, and
both paper sources.

## Hardware / software assumptions

- Any x86-64 or arm64 machine with ≥16 GB RAM (the heaviest step builds a
  dense ~53k × 10k feature matrix); no GPU.
- Python 3.10+ with `numpy`, `scikit-learn`, `matplotlib`, pinned in
  root `requirements.txt`.
- TeX Live (pdflatex + bibtex) to build the papers.
- Runtimes: public-data experiments, minutes; each PAN-2012 experiment,
  roughly 10–30 minutes on a laptop.

## Environment setup

```bash
git clone <artifact-url> && cd <repo>
pip install -r requirements.txt
```

## Reproduction: no restricted data required

```bash
bash scripts/reproduce_public.sh
```

Runs the synthetic S-curve sanity check and the M8 Byzantine/SPRT
simulations; runs the F3 reciprocity analysis automatically iff the gated
GT-HarmBench CSV is present at the path documented in
`data/gt_harmbench/README.md`, otherwise skips it with an explanation.
Outputs land in `experiments/results/` and `validation/synthetic/results/`.

## Reproduction: real-data claims (PAN 2012 required)

PAN 2012 is public research data distributed by the PAN organizers and is
NOT redistributed here; acquisition steps are in `data/pan12/README.md`.
Place the training XML and predator list under `data/pan12/train/`, then:

```bash
python3 experiments/exp_trajectory_lift.py                    # RQ1/RQ3
python3 experiments/exp_m3_author_split.py                    # split prerequisite
python3 experiments/exp_m3_frontier.py                        # RQ2
python3 experiments/exp_perturbation_sweep.py                 # RQ4 (conv-level split)
python3 experiments/exp_perturbation_sweep_author_disjoint.py # RQ4 (author-disjoint)
python3 experiments/exp_perturbation_model_controls.py        # RQ4 controls + paired tests
python3 experiments/exp_perturbation_second_family.py         # RQ4 second family
python3 experiments/exp_fp_substrate.py                       # RQ5
```

Every script fails gracefully with setup instructions (no stack trace) if
the data is absent, and none prints raw corpus text.

## Expected outputs

Each script writes JSON (+ PDF/PNG figures) to `experiments/results/`,
matching the committed files up to floating-point noise (see Known
limitations). Companion `perturbation_sanity_checks*.json` files record
per-condition label stability, split hashes, author-overlap checks, and
text/order/length change statistics.

## Claim-check procedure

```bash
python3 scripts/check_claims.py        # expect: "All 31 claim checks passed."
python3 scripts/build_paper_tables.py  # regenerates paper/tables/*.tex from JSONs
```

`check_claims.py` re-derives every headline number in the README (the same
numbers the paper reports) from the committed JSONs and fails on drift;
`build_paper_tables.py` regenerates every result table, so paper tables
cannot silently diverge from evidence.

## Paper builds

```bash
# long-form v9 draft
pdflatex -interaction=nonstopmode -halt-on-error \
  -jobname=Adversarial_Intent_Telemetry_draft_v9 \
  -output-directory=paper/build \
  Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.tex   # run twice

# USENIX-oriented draft (run from repo root)
pdflatex -interaction=nonstopmode -halt-on-error \
  -output-directory=paper/build -jobname=usenix_draft \
  paper/usenix/adversarial_intent_telemetry_usenix.tex
bibtex paper/build/usenix_draft
# then pdflatex twice more
```

## Known limitations

- PAN 2012 and GT-HarmBench cannot be redistributed (acquisition documented
  per-dataset under `data/`).
- Figure rendering varies slightly with matplotlib version.
- All experiments are seeded (SEED=20260514 plus enumerated perturbation
  seeds), but BLAS build differences can perturb the last decimal of some
  metrics; `check_claims.py` compares at reported rounding.
- The perturbation families are rule-based; nothing in the artifact
  generates abuse content, grooming material, or operational evasion
  guidance, and no corpus text is sent to any external service.

## Data acquisition notes

- **PAN 2012**: from the PAN organizers per `data/pan12/README.md`
  (public/open, sensitive online-safety data; handle accordingly).
- **GT-HarmBench**: gated HuggingFace dataset per
  `data/gt_harmbench/README.md`; only needed for the analytical F3 result.
