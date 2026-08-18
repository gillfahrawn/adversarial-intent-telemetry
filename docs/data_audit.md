# Data audit: tracked files under `data/`

Scope: every `.jsonl`, `.json`, `.csv`, and `.txt` file tracked in git under
`data/` (per `git ls-files | grep '^data/'`), checked for raw or near-raw PAN
2012 conversation text. Method: no sensitive snippets are reproduced in this
document or were printed during the audit; overlap was measured by hashing
8-word shingles (lowercased, tokenized) from the restricted PAN 2012 training
XML and checking what fraction of each tracked file's dialogue-turn shingles
collide with that set. An 8-word exact match is not plausible by chance for
natural-language text; a match rate near 0% is expected of independently
generated text, and a high per-turn match rate (many/most consecutive
8-grams in one turn matching) indicates the turn is copied, not generated.

> **Posture recalibration (2026-07-06).** PAN 2012 is public/open research
> data (Inches & Crestani, CLEF 2012), not private or confidential data. The
> finding below was initially framed as a high-severity leak; that framing was
> too strong. The correct framing: the file redistributed verbatim excerpts of
> a public-but-sensitive corpus outside the PAN organizers' own distribution
> channel, without provenance documentation, in a repo that states it does not
> redistribute the corpus. That is a provenance/consistency problem, not a
> secret leak. The file remains untracked going forward (done); **no git
> history rewrite is planned or needed** unless a specific PAN license
> violation is identified or the repository owner decides otherwise.

## Finding: `data/pan_annotated/regenerated_trajectories_noisy.jsonl` contains verbatim PAN 2012 text

**Severity (recalibrated): moderate — documentation/provenance issue with a
public-but-sensitive corpus.** The file is committed (`d868234`) and on the
public remote.

- `tools/inject_discourse_noise.py` builds an `empirical_message_bank` by
  reading real messages directly out of
  `data/pan12/train/pan12-sexual-predator-identification-training-corpus-2012-05-01.xml`
  (`load_empirical_message_bank`, filtered to non-predator authors, message
  length < 15 words). Its `_execute_strategy` "swap" branch
  (`strategy_idx == 2`) does `random.choice(self.msg_bank)` — i.e. it
  replaces a synthetic turn's content with a **verbatim message pulled from
  the real, restricted PAN 2012 corpus**.
- `main()` in that script writes its output directly to
  `data/pan_annotated/regenerated_trajectories_noisy.jsonl` — the exact
  tracked path.
- Shingle audit on the 20 records in this file: 222 total 8-word shingles
  extracted from turn text, 76 (34%) collide with the real-PAN shingle set.
  Several individual turns match 100% of their own 8-grams against real PAN
  text (e.g. one 279-character turn produced 35 shingles, all 35 present in
  the PAN 2012 shingle set) — i.e., those turns are not paraphrased or
  generated, they are the real corpus message, unmodified.
- This directly contradicts `CLAUDE.md`'s statement that raw PAN 2012 is "not
  redistributed," for this one file.

Remediation status:
1. **Done** — the file was removed from tracking (`git rm --cached`) and
   explicitly gitignored, so it will not be re-committed. It stays on local
   disk for reproducibility.
2. **Not planned** — git history purge (`git filter-repo`/BFG). Given the
   recalibrated posture (public research corpus, provenance issue rather than
   confidentiality breach), rewriting public history is disproportionate
   unless a specific PAN license violation is identified or the owner
   explicitly requests it.
3. **Optional future work** — regenerate a noisy-condition fixture with the
   retrieval-swap bank drawn from synthetic messages instead of the corpus,
   if a tracked noisy fixture is ever needed again.

## Other tracked files under `data/`: structural features / low-risk synthetic only

| File | Contains raw text? | Assessment |
|---|---|---|
| `data/agentic_ncmec/pan_ncmec_trajectories.jsonl` | Turn `content` fields present, `data_source: pan2012_phase_adapted_synthetic` (LLM-generated from PAN scaffolds, not verbatim). Shingle audit: 3/152,768 8-grams (0.002%) collide with real PAN text, each collision only 1 shingle within a 34-47 shingle turn (2-3%) — consistent with coincidental common short phrases, not copying. | Low risk. Keep public; re-audit if the generation pipeline changes. |
| `data/pan_annotated/adapted_trajectories.jsonl` | Same generation pipeline and same shingle-overlap profile as above (spot-checked records are identical to the NCMEC file's pre-injection state). | Low risk. Keep public. |
| `data/pan_annotated/regenerated_trajectories.jsonl` | Turn `content` present; `topic`/`template` fields show synthetic hobby-scenario prompts (e.g. a fictional hobby topic), no `data_source` tag. Shingle audit: 0/286 8-grams collide with real PAN text. | Low risk — appears to be pure Tier-0 synthetic generation (pre-noise-injection input to the file above). Not currently listed in `CLAUDE.md` §3; recommend adding an entry so its provenance is documented rather than left implicit. |
| `data/pan_annotated/pan_manifests_v2.jsonl` | No raw text field. Keys: `conversation_id`, `data_source`, `adversarial`, `predator_author_id`, `n_turns`, `manifest`, `manifest_entropy_bits`, `entropy_gate_pass`. `predator_author_id` is a PAN 2012 author ID (an opaque identifier from the original corpus, not text), not free text. | Structural features and IDs only. Safe to keep public. |
| `experiments/results/pan_manifest_annotated.jsonl` | Same key structure as above, no raw text. | Structural features and IDs only. Safe to keep public. |
| `data/README.md`, `data/pan12/README.md`, `data/pan12/test/readme.md`, `data/pan12/train/README.md`, `data/gt_harmbench/README.md` | Documentation only. | Safe. Replaced from `placeholder` in this pass — see those files. |

## Files checked and confirmed absent from tracking (local-only, correctly gitignored)

`data/pan12/train/*.xml`, `data/pan12/test/*.xml`, `data/pan12/train/*predators*.txt`,
`data/gt_harmbench/GTHarmbenchdatatrain00000of00001.csv`,
`data/agentic_ncmec/injection_report.json`, `data/pan_annotated/adaptation_report.json`,
`data/pan_annotated/annotation_report_v2.json`, `data/nmec/ncmec_behavioral_constraints_2025.json`.
None of these were pushed; no action needed beyond confirming `data/.gitignore`
continues to exclude them (see the explicit-exception list added to that file
so future re-generation of the *tracked* derived files doesn't get silently
dropped, while the raw/gated sources stay untracked by default).

## Non-`data/` tracked result files (spot-checked, out of the requested scope, no action needed)

`experiments/results/*.csv` and `*.txt` (continuity metrics, structural overlap
matrix, causality/observer-divergence reports) contain only numeric feature
columns or aggregate statistics — no message text. `experiments/results/pan_manifest_annotated.jsonl`
is covered above.
