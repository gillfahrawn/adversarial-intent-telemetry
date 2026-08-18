# data/pan12/ — PAN 2012 Sexual Predator Identification corpus

## What this is

The PAN 2012 Sexual Predator Identification (SPI) corpus is a public research
dataset of real human chat-log conversations released for the PAN 2012 shared
task at CLEF, a subset of which are labeled as containing a sexual predator
(grooming) participant. This repository uses it as the empirical substrate for
every "real" result: the per-message classifier, the MinHash signature
frontier, the trajectory-model lift/evasion experiments, and the perturbation
sweep all run on this corpus.

**Citation**: Inches, G. & Crestani, F. (2012). *Overview of the International
Sexual Predator Identification Competition at PAN-2012.* CLEF 2012 Evaluation
Labs and Workshop. The corpus is distributed by the PAN shared-task organizers
(pan.webis.de) under their access terms.

## Data posture: public/open, but sensitive

PAN 2012 is **public, open research data** — it is not private or confidential.
It is also **sensitive online-safety data**: the conversations are real chat
transcripts related to grooming investigations. This repository's handling
rules follow from that combination:

- **Not redistributed here.** The corpus XML is excluded from git via the root
  `.gitignore` (`data/pan12/`). Users should obtain it from the original PAN
  source so that provenance and the organizers' access terms are preserved,
  not because the data is secret. Only this documentation is tracked.
- **Raw excerpts are not printed or foregrounded.** Scripts may process the
  text locally, but analysis output, logs, README, docs, and result JSONs
  report structural/statistical features only (lengths, timing, label counts,
  similarity scores, aggregate rates) — never conversation text. This is a
  minimization practice for sensitive content, not a secrecy requirement.
- Do not build or publish a re-identification pipeline against the corpus's
  author IDs.

## What is expected on disk (not provided by `git clone`)

```
data/pan12/
  train/
    pan12-sexual-predator-identification-training-corpus-2012-05-01.xml
    pan12-sexual-predator-identification-training-corpus-predators-2012-05-01.txt
    README.md   (this subdirectory's notes — tracked)
  test/
    pan12-sexual-predator-identification-test-corpus-2012-05-17.xml
    readme.md   (this subdirectory's notes — tracked)
```

`experiments/exp_m3_author_split.py`, `exp_m3_frontier.py`,
`exp_trajectory_lift.py`, `exp_perturbation_sweep.py`, `exp_fp_substrate.py`,
and `exp_annotate_pan_manifest.py` read from `train/` at the paths above; none
of them currently read from `test/` (the "test" split reported in results is a
held-out partition of the training XML, not this separate test-corpus file —
see each script's docstring for its exact split logic).

## How to obtain it

Request the corpus through the PAN shared-task organizers' current access
process (pan.webis.de, Sexual Predator Identification 2012). Once obtained,
place the files at the paths above. Scripts that need the corpus fail with a
pointer to this file when it is absent.

## Temporal-domain caveat

This corpus validates detection of **human grooming conversations from 2012**.
Results on it do not validate detection of 2026 agentic automation; that
mismatch is stated wherever PAN-derived numbers are reported (see README.md
and CLAUDE.md).
