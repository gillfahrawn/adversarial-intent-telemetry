# USENIX migration plan — v9 empirical paper

> **STATUS (2026-07-08, official-style pass): the official USENIX style file
> is now present and used.** `paper/usenix/usenix.sty` (the classic USENIX
> `usenix.sty`, which selects two-column Times via `mathptmx`, and loads
> `fontenc`, `inputenc`, `microtype`, `cite`, `url`/`breakurl`, `xcolor`,
> and colored `hyperref`) is in the repo. The source now loads it and no
> longer emulates geometry when it is present. Verified in the build log:
> `usenix.sty` + `mathptmx` load, `geometry.sty` does **not**, and there is
> no hyperref option clash (the previously-separate `hyperref`/`xurl`/
> `fontenc` loads were moved into the fallback-only branch).
>
> **Style-detection detail (important for the documented compile command).**
> The paper is compiled from the repository root, but TeX does not search
> the main file's own directory (`paper/usenix/`) for `usenix.sty`. The
> `\IfFileExists` hook therefore checks two locations:
> (1) `usenix.sty` on the input path (works when compiling from
> `paper/usenix/` or with `TEXINPUTS=./paper/usenix:`), then
> (2) `paper/usenix/usenix.sty` root-relative, loaded via
> `\makeatletter\input{...}\makeatother` (the `\makeatletter` guard is
> required so `usenix.sty`'s `\if@twocolumn` parses; without it the file
> tries to `\input` the obsolete `twocolumn.sty` and aborts), then
> (3) the geometry fallback if neither exists. This makes the exact
> documented bare command below build with the official style from the repo
> root, with no `TEXINPUTS` needed.
>
> **Do not edit `paper/usenix/usenix.sty`** (official file, left verbatim).
>
> The USENIX-oriented source at
> `paper/usenix/adversarial_intent_telemetry_usenix.tex` compiles with the
> official style to **10 two-column pages** (both non-anonymous and
> anonymous), with **0 undefined references, 0 overfull boxes, 0 real
> BibTeX warnings** (the `.blg` "warning$ -- 0" line is BibTeX's
> function-usage stat, not a warning), exit 0 through
> pdflatex + bibtex + pdflatex×2. 41 *underfull* hboxes remain (23 at
> badness 10000); these are cosmetic, caused by unbreakable `\texttt{}`
> code spans and URLs in the narrow two-column measure, and do not intrude
> into the margins. Compile from the repository root:
>
> ```
> pdflatex -interaction=nonstopmode -halt-on-error \
>   -output-directory=paper/build -jobname=usenix_draft \
>   paper/usenix/adversarial_intent_telemetry_usenix.tex
> bibtex paper/build/usenix_draft
> pdflatex ...   # twice more
> ```
>
> For the anonymous build, temporarily flip `\anonymousfalse` →
> `\anonymoustrue` (the `\anonymous...` line in the preamble), recompile
> with `-jobname=usenix_draft_anonymous`, then flip back; do not leave the
> checked-in source in anonymous mode.
>
> **Body-length / page-count breakdown (2026-07-08, official style, from
> the `.aux` `\newlabel` page anchors; identical for both builds):**
>
> | Milestone | Page (official style) |
> |---|---|
> | Introduction starts | p.1 |
> | Results starts | p.4 |
> | Discussion starts | p.7 |
> | Limitations starts | p.7 |
> | Conclusion starts (main body ends here) | p.7 |
> | Ethical Considerations starts | p.7 |
> | Open Science starts | p.8 |
> | References start | ~p.8/9 (immediately after Open Science; `plain` BibTeX emits no `\newlabel` anchor, read off section flow) |
> | Artifact Appendix starts | p.9 |
> | **Total PDF pages** | **10** (both non-anonymous and anonymous) |
>
> Main body (Introduction through Limitations, before Ethical
> Considerations) runs ~7 pages; Ethical Considerations + Open Science
> together are ~1.5 pages; references + the artifact appendix occupy the
> last ~1.5 pages. Under the official style the non-anonymous and anonymous
> builds now land on the same 10 pages (the earlier 9/10 split was a
> fallback-geometry artifact). If the target CFP mandates a different
> official class than this `usenix.sty` (e.g. a year-specific
> `usenix20xx_v3.1.sty`), drop it next to the `.tex` and extend the
> `\IfFileExists` chain; column measure could then shift the table above.
>
> Cuts applied are recorded in `paper/length_reduction_plan.md`;
> anonymization steps in `paper/anonymization_checklist.md`; the AE
> appendix master in `paper/artifact_appendix.md`. The v9 single-column
> draft remains authoritative long-form and still compiles. The material
> below this banner is the original pre-conversion plan, kept for
> reference.

Plan for converting `Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.tex`
(draft v9.0, single-column article class) to the USENIX Security format.
Written 2026-07-06. The official USENIX style file is **not** present in the
repo, so no conversion was attempted in this pass (per instructions: no
guesswork). The current draft compiles cleanly and stays authoritative until
the template switch.

## Current state

- **Page count:** 27 pages (grew from 24 in the RQ4 stress-test pass, which
  added the author-disjoint replication, aggregation/order-control, and
  paired-test tables), 11pt single-column `article`, letterpaper, 1in
  margins, 1.12 line stretch.
- **Estimated two-column equivalent:** roughly 14–16 pages in
  `usenix2019_v3.sty` (10pt, two-column) including references and the
  manifest appendix — over a typical 13-page body limit.
  Expect to cut 2–3 pages (candidates below; the original conversation-level
  sweep table is now also a merge candidate with the author-disjoint one).
- **Compile command in use** (root of repo; `-jobname` keeps the v9 output
  name and protects the legacy v8.1 PDF in the repo root):

  ```
  pdflatex -interaction=nonstopmode -halt-on-error \
    -output-directory=paper/build \
    -jobname=Adversarial_Intent_Telemetry_draft_v9 \
    Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.tex
  ```

## Files needed

- `usenix2019_v3.sty` (or the year-specific successor from the CFP) — not in
  repo; download from usenix.org at migration time.
- `references.bib` — convert the numbered enumerate to BibTeX (see
  `bibliography_audit.md` for per-entry dispositions); use `plain` or the
  style the template mandates.
- Recommended: rename the source to `paper/adversarial_intent_telemetry.tex`
  at migration time (the current filename still carries the v8.1 design-doc
  name; keep the current file compiling until the new one builds).

## Template-conversion risk list

Likely to break or need rework at column width (~3.33in):

- **Evidence and Validity Matrix (longtable, 3 cols)** — must become a
  `table*` (full-width) or be tightened; `longtable` does not work in
  two-column mode. Highest-effort item.
- **Taxonomy table (tabularx, full text width)** — `table*` and probably a
  smaller font; consider cutting the "Known Evasion" column.
- **Manifest appendix longtable** — same `longtable` problem; convert to a
  `table*` series or move to the artifact repository entirely (candidate cut).
- **Perturbation-sweep table (6 cols with ± std)** — fits `table*`; may fit a
  single column if the ± values move to a footnote.
- **Figures** (`m3_frontier.pdf`, `perturbation_sweep.pdf`,
  `fp_substrate.pdf`) — generated at ~9in widths with fonts sized for that;
  legibility at 3.33in must be checked, and regenerating with larger fonts
  from the JSONs is the clean fix (figure scripts already exist).
- **Algorithm + JSON listing** — fit one column but are space-hungry;
  candidates for compression or artifact-only status.
- `titlesec`/`fancyhdr`/`geometry`/`setspace` customizations must all be
  dropped (the template owns layout).

## Length reduction candidates (in order)

1. Manifest appendix → artifact repo (saves ~2.5 pages; keep a half-page
   summary table).
2. Algorithm 1 + wire-format listing → compress to prose + artifact pointer
   (~1 page).
3. §5 design-under-test prose → trim taxonomy table and intuition text
   (~0.5 page).
4. §3 background → the motivation paragraphs can lose the CVE inventory
   (~0.3 page).

## Anonymization plan (double-blind)

A LaTeX switch is already in place in the preamble:

```tex
\newif\ifanonymous
\anonymousfalse   % flip to \anonymoustrue for submission
```

Currently it gates only the author block. For submission, additionally:

- **Author name:** handled by the switch.
- **ACCO affiliation:** handled by the switch; also remove/neutralize the
  ACCO mention in the abstract-page footer if any, and reconsider ref [16]
  (ACCO's own report — either cite in third person or drop; see
  bibliography audit).
- **Repo URL (ref [19] and §6 reproducibility text):** replace with an
  anonymized artifact link (e.g., Zenodo anonymous deposit or the
  conference's artifact submission mechanism). Grep targets:
  `github.com/gillfahrawn`, `[19]`.
- **v8.1 design-document provenance:** the paper repeatedly says "a prior
  design document (v8.1, included with this artifact)" — fine when
  anonymized as long as the design doc shipped with the artifact is itself
  scrubbed of the author block. Add that scrub to the artifact checklist.
- **Header:** `\fancyhead` carries no author info (title only) — but the
  template will replace headers anyway.
- **Acknowledgments:** none present; nothing to mask.
- **Self-citations:** [16] is the only one; treat per above.

## Artifact appendix expectations (USENIX AE)

- Artifact abstract; hardware/software requirements (Python 3, numpy,
  scikit-learn, matplotlib; no GPU); expected runtimes.
- Two-tier reproduction story already exists and should be stated:
  `scripts/reproduce_public.sh` (no restricted data) vs. PAN-2012-dependent
  experiments (obtain corpus from PAN organizers; documented in
  `data/pan12/README.md`).
- `scripts/check_claims.py` (README/number consistency) and
  `scripts/build_paper_tables.py` (paper tables from JSON) are the claim
  verification hooks — surface both in the appendix.
- Data ethics note for AE reviewers: PAN 2012 is public but sensitive; the
  artifact never prints raw dialogue.

## Known compile warnings (current draft)

Two-pass pdflatex: exit 0, zero undefined references, zero missing figures.
Remaining overfull hboxes, all cosmetic (≤ 6.6pt ≈ 2.3mm):

- taxonomy table row (~3.0pt)
- a methods paragraph head (~6.6pt)
- appendix `phase_transition` row (~1.6pt)
- appendix minimum-entropy paragraph (~6.3pt)

These will be re-evaluated after the template switch (different measure), so
fixing them now is wasted effort.

## Ethics section

A standalone "Ethics, Safety, and Governance Non-Claims" section (§9) now
exists and covers data posture, no client-side scanning, no deployment
recommendation, false-positive harm populations, human review/appeal, and
no-compliance claims — this maps directly onto the USENIX ethics
considerations requirement; convert to the template's expected unnumbered
section if the CFP requires that form.
