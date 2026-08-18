# Anonymization checklist — double-blind submission readiness

Applies to `paper/usenix/adversarial_intent_telemetry_usenix.tex` (the
submission source). Mechanism: the `\ifanonymous` boolean in the preamble;
flip `\anonymousfalse` → `\anonymoustrue`. Verified 2026-07-07: the
anonymous build compiles (exit 0) and the author strings disappear from the
document.

**Re-verified 2026-07-08** by rendering `usenix_draft_anonymous.pdf` to text
(`gs -sDEVICE=txtwrite`) and grepping it for `fahrawn`, `gillfahrawn`, `acco`,
`alliance to counter`, `/users/`, `.claude`, `linkedin`, `gmail`: **0 hits**.
This re-verification caught a real leak (see next paragraph), so it should be
repeated after any change touching `\cite{artifact2026}` or `references.bib`.

**Re-verified again 2026-07-08 (official-style pass)** after switching the
source to the official `paper/usenix/usenix.sty` and the em-dash/language
copyedit. The anonymous build was recompiled with the official style
(`-jobname=usenix_draft_anonymous`, 10 pages, 0 overfull) and re-rendered to
text; the scan for `fahrawn`, `gill`, `gillfahrawn`, `gmail`, `acco`,
`alliance to counter`, `github.com`, `github.com/gillfahrawn`, `/users/`,
`.claude`, `anonymized-artifact-url`, `linkedin` returned **0 hits**, and no
em-dash (`—`) renders. The staged artifact was resynced (updated `.tex` in
`\anonymoustrue` mode with the author `\else` branch physically removed, the
copyedited `artifact_appendix.md`, and `usenix.sty` so reviewers can build
with the official style); the staged anonymous PDF re-scanned clean apart
from the intended `ANONYMIZED-ARTIFACT-URL` placeholder.

**Leak found and fixed 2026-07-08**: `\cite{artifact2026}` is used twice in
the body (Introduction, Results-preview list) *outside* any `\ifanonymous`
gate, so even in anonymous mode those citations pulled the `artifact2026`
bibliography entry — and its `howpublished` field held the real
`github.com/gillfahrawn/...` URL unconditionally — into the reference list.
The PDF-text scan confirmed the URL was present on the rendered anonymous
page. Fixed by making the `howpublished` field itself conditional on
`\ifanonymous` inside `paper/references.bib` (BibTeX passes the field
through as literal text; LaTeX expands the macro when it processes the
`.bbl`), so the anonymized text or the real URL is selected per build
regardless of which citation site pulls the entry in. Re-verified clean by
the text scan above. The former "manual bib swap" item below is superseded
by this fix — no manual step remains for this entry.

## Gated by the switch (already done)

- [x] **Author block** — replaced by "Anonymous submission" under
  `\anonymoustrue`.
- [x] **Open Science artifact pointer** — anonymous branch says "available
  to reviewers via the anonymized link in the submission system" with a
  `TODO(anonymization)` to insert the actual link; non-anonymous branch
  cites `artifact2026`.
- [x] **`paper/references.bib` → `artifact2026` URL** — the `howpublished`
  field is now `\ifanonymous`-gated directly in the `.bib` entry, so both
  `\cite{artifact2026}` sites (one of which was previously ungated) render
  the anonymized placeholder text under `\anonymoustrue`. Confirmed by the
  PDF-text re-scan (0 hits for `gillfahrawn`/`fahrawn`). Still needed before
  final submission: replace the placeholder text with an actual anonymized
  deposit link (Zenodo anonymous / conference artifact system) — see the
  open item below.

## NOT gated by the switch — manual steps before submission

- [ ] **Anonymized deposit link**: the `\ifanonymous` branch of
  `artifact2026` currently reads "Anonymized artifact link provided to
  reviewers via the submission system" — a placeholder. Before submission,
  either upload the artifact to an anonymous host (anonymous Zenodo/OSF,
  the conference's artifact system) and paste the real anonymized link, or
  confirm the venue's submission system handles artifact linking separately
  and this sentence can stay generic.
- [ ] **`paper/references.bib` → `acco2024`**: report by the author's own
  organization (ACCO), cited once in the v9 draft's background; the USENIX
  source does **not** cite it, so for the USENIX submission no action is
  needed unless it is re-added. Entry carries an ANONYMIZATION note.
- [ ] **Bundled v8.1 design document**: the paper repeatedly identifies "a
  prior design document (v8.1, included with the artifact)". The PDF in the
  artifact carries the author's name and ACCO affiliation on its title page
  — scrub or replace it in the anonymized artifact deposit. (Reviewers can
  otherwise deanonymize in one click.)
- [ ] **Artifact repository content**: README contact section (name, email,
  LinkedIn), `CLAUDE.md`/`AGENTS.md` author references, and absolute paths
  in any stale artifacts. The anonymized deposit should be built from a
  scrubbed export, not a direct repo mirror.

## Self-identifying text inventory (grep targets)

| Pattern | Where it appears | Handling |
|---|---|---|
| `Fahrawn Gill` | author block (both .tex sources) | switch-gated in USENIX source; v9 draft is not the submission source |
| `ACCO` / `Alliance to Counter Crime Online` | author block; `acco2024` bib entry | switch-gated; bib entry uncited in USENIX source |
| `gillfahrawn` / GitHub URL | `artifact2026` bib entry (both `\cite` sites); README | fixed: `howpublished` field is `\ifanonymous`-gated in the `.bib` entry itself; artifact deposit scrub still needed for the staged package |
| v8.1 design doc self-reference | Intro, Design Under Test, Open Science | fine once the bundled PDF is scrubbed; the text itself does not name the author |
| Acknowledgments / personal notes | none present in either source | nothing to do |

## Self-citation policy

The only self-affiliated citation is `acco2024` (not cited in the USENIX
source). The design document is the paper's own object of study; USENIX
double-blind convention allows citing it as "a prior design document
included with the artifact" without naming the author, which is exactly how
the text reads.
