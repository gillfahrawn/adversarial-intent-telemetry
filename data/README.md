# data/

This directory holds inputs and derived artifacts for the experiments in
`experiments/` and `tools/`. It mixes three kinds of content with different
redistribution status. Check the table below before assuming a path exists
in a fresh clone.

| Subdirectory | Contains | Redistributed in this repo? |
|---|---|---|
| `pan12/` | PAN 2012 Sexual Predator Identification corpus (public research data; real human chat logs, 2012) | **No.** Public/open but sensitive — obtain from the PAN organizers so provenance and access terms are preserved. See `pan12/README.md`. Only documentation is tracked; the XML is gitignored. |
| `gt_harmbench/` | GT-HarmBench game-theoretic interaction dataset | **No.** Gated HuggingFace dataset. See `gt_harmbench/README.md`. |
| `pan_annotated/` | Derived feature manifests and LLM-generated phase-adapted trajectories built from PAN 2012 | Partially. Structural-feature files (`pan_manifests_v2.jsonl`) and synthetic-generation outputs whose provenance has been text-audited are tracked; see `docs/data_audit.md` for exactly which files and why. |
| `agentic_ncmec/` | Tier-2 trajectories combining PAN-derived structure with an NCMEC-2025-prior-sampled telemetry layer | `pan_ncmec_trajectories.jsonl` is tracked; text-audited (see `docs/data_audit.md`). |
| `nmec/` | NCMEC 2025 behavioral constraint priors (summary statistics, not conversation text) | Local artifact; not currently tracked. |

## Sensitive content handling

PAN 2012 is public/open research data, but it is sensitive online-safety
content. Do not write code, prompts, fixtures, or documentation in this
repository that generates, requests, or reproduces explicit child sexual
abuse content, grooming scripts, or operational abuse examples. Every
experiment that touches PAN 2012 or the NCMEC priors reports only
structural/statistical features (message counts, timing, lexical-category
flags, Jaccard similarity, phase labels, aggregate rates) — raw conversation
text is processed locally where needed but never printed, logged, or
committed. Where LLM-generated dialogue is used for ablation, it uses
synthetic scenarios explicitly unrelated to real minors. See
`docs/data_audit.md` for the audit that checks tracked files under this
directory for verbatim inclusion of corpus text, and for one confirmed
finding and its remediation.

## Obtaining externally distributed datasets

- **PAN 2012**: see `pan12/README.md`.
- **GT-HarmBench**: see `gt_harmbench/README.md`.

Neither dataset should be committed to this repository. `data/.gitignore`
excludes raw corpora by extension; if you add a new derived file that should
be public, add an explicit exception there (see the comments in that file)
rather than force-adding around the ignore rule.
