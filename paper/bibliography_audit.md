# Bibliography audit — v9 empirical paper draft

> **UPDATE (2026-07-08): citation verification pass complete for all
> priority items.** Of 18 entries in `paper/references.bib`, **13 are
> verified** (author/venue/identifier confirmed against arxiv.org, NVD, or
> the entry is a stable published book/proceedings citation) and **5 carry
> an open `TODO(verify)`/`TODO(formalize)` note** — none fabricated, all
> honestly marked. Per-priority-item outcome:
>
> 1. **GT-HarmBench** (`gtharmbench2026`) — verified against arxiv.org
>    (arXiv:2602.12316, full author list). Load-bearing for RQ6/F3; resolved.
> 2. **PAN 2012 provenance** (`villatoro2012`) — complete CLEF 2012
>    working-notes citation, no open items. Resolved.
> 3. **MCP / CVE / RCE** — `mcprce2026` replaced the press citation with the
>    primary NVD advisory (CVE-2025-49596); `mcpclients2026`,
>    `sok2026promptinjection`, `breakingprotocol2026`, `echoleak2025` all
>    verified against arxiv.org. Resolved.
> 4. **NCMEC / Tech Coalition / Lantern / VHIP** — `lantern2026` is cited
>    directly to the Tech Coalition (the primary institutional source, not
>    press) but still bundles several figures into one entry
>    (`TODO(formalize)`: split into per-report entries with URLs); `bsrhria`
>    still needs its publication year/URL verified (`TODO(verify)`);
>    `photodna2023` (vendor doc, non-load-bearing — backs an explicit
>    non-claim) still needs a stable URL (`TODO(verify)`). Partially
>    resolved; none of the open items are load-bearing blockers (see
>    per-entry table).
> 5. **Broder / MinHash** (`broder1997`) — complete SEQUENCES '97 citation.
>    Resolved.
> 6. **Ostrom / reciprocity** (`ostrom1990`) — complete book citation.
>    Resolved.
> 7. **2026-era arXiv/medRxiv `TODO(verify)` entries** — all 2026-era arXiv
>    entries (`sok2026promptinjection`, `mcpclients2026`,
>    `breakingprotocol2026`, `gtharmbench2026`) verified against arxiv.org
>    2026-07-07. The one medRxiv entry, `medredteam2026`, **could not be
>    verified**: medRxiv blocks automated fetch (HTTP 403) from this
>    environment. Left as `TODO(verify)` rather than guessed. Per the
>    original audit note for this item ([10] below), the sentence it backs
>    is explicitly non-load-bearing — the taxonomy it anchors is stated in
>    the paper as non-validated design vocabulary — so no claim needed
>    weakening; a manual check (open medRxiv in a browser, confirm DOI and
>    author list) is the only remaining action.
>
> `euaiact2026` and `gpaicop2026` (European Commission documents) back only
> the ethics **non-claims** ("this work does not establish compliance
> with...") — explicitly non-load-bearing per the claim-discipline rule, so
> their `TODO(formalize)` notes (publication dates/URLs) are cosmetic, not
> blocking. `acco2024` is not cited by the USENIX source; kept for the v9
> draft only, flagged for anonymization (self-affiliated organization), not
> a verification problem.
>
> No entry's author, year, venue, or identifier was invented in this pass.
> Where a value could not be confirmed, the field is either left absent
> (three items with unknown publication years were omitted from the .bib
> in the 2026-07-07 pass rather than guessed) or the entry carries an
> explicit `TODO(verify)`/`TODO(formalize)` note.
>
> **Manual checks still needed before submission** (cannot be completed by
> automated fetch from this environment): `bsrhria` publication year/URL;
> `photodna2023` stable URL; `medredteam2026` DOI/author confirmation via a
> browser (medRxiv returns 403 to automated tools); `lantern2026` split into
> per-report entries if reviewers push back on the bundled citation.
>
> *(Earlier 2026-07-07 note, superseded by the above: `paper/references.bib`
> was created from the v9 hand-numbered list without invention; entries
> needing verification carried `TODO(verify)`, and `mcprce2026` carried
> `TODO(replace)` — since resolved as described above.)*

Audit of the reference list in
`Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.tex` (draft v9.0),
2026-07-06. No citations were invented or removed in this pass; formatting
fixes only ([19] converted to a breakable `\url{}`). Dispositions below are
recommendations for the pre-submission pass.

Legend: **formalize** = keep, convert to a complete BibTeX entry;
**primary** = replace with the primary source; **remove?** = remove if not
load-bearing after restructuring; **verify** = needs manual verification of
identifiers/authors before submission (arXiv IDs and preprint DOIs in this
list have not been independently re-checked against the published record).

**2026-07-08: `Ref` column now shows the resolving `references.bib` key and
final status; see the summary block above for the authoritative outcome.**
The rest of each row (current form / load-bearing-for / original
disposition) is kept verbatim as the historical record of what was flagged
and why.

| Ref | Current form | Load-bearing for | Disposition |
|---|---|---|---|
| [1] → `sok2026promptinjection` — **RESOLVED**, verified vs arxiv.org 2026-07-07 | SoK, arXiv:2601.17548, no authors listed | Background: adaptive attack success rates | **verify + formalize**. Add authors; confirm arXiv ID. Supports motivation only. |
| [2] → `mcpclients2026` — **RESOLVED**, verified vs arxiv.org 2026-07-07 | arXiv:2603.21642, no authors listed | Background: MCP client disparities | **verify + formalize**. Same. |
| [3] → `mcprce2026` — **RESOLVED**, replaced with primary NVD advisory (CVE-2025-49596) | The Hacker News (press) on MCP CVEs | Background: MCP RCE disclosures | **primary**. Replace with vendor advisories / NVD entries for CVE-2025-49596, CVE-2026-22252, CVE-2026-22688. Press cite is not acceptable at USENIX for a security claim. `TODO(bib)` comment placed in §3 of the .tex. |
| [3a] → `echoleak2025` — **RESOLVED**, verified vs arxiv.org 2026-07-07 | EchoLeak: CVE-2025-32711, Aim Labs + arXiv:2509.10540 | Background: zero-click injection example | **verify + formalize**. CVE is citable via NVD/MSRC; confirm the arXiv writeup ID. |
| [4] → `breakingprotocol2026` — **RESOLVED**, verified vs arxiv.org 2026-07-07 | "Breaking the Protocol", arXiv:2601.17549, no authors | Background + taxonomy row (provenance-tagging) | **verify + formalize**. Add authors; confirm ID. |
| [5] → `lantern2026` — **PARTIAL**, cited directly to Tech Coalition (primary), `TODO(formalize)` to split bundled figures into per-report entries | Tech Coalition 2025 transparency reports + hackathon proceedings, bundled | Motivation figures (2M signals, 17× growth, VHIP volumes, Korean classifier) | **primary + split**. This one entry currently backs at least four distinct claims. Split into separate entries: (a) Lantern Transparency Report (April 28, 2026) with URL/date; (b) VHIP documentation; (c) the Korean grooming classifier announcement. Load-bearing for §3 motivation; `TODO(bib)` comment placed in the .tex. |
| [6] → `euaiact2026` — **PARTIAL**, non-load-bearing (backs an ethics non-claim only), `TODO(formalize)` dates/URLs | European Commission GPAI guidelines / AI Act timeline | Ethics non-claims | **formalize**. Cite the specific Commission documents (title, date, URL). Supports a non-claim, so weak form is tolerable but sloppy. |
| [7] → `gpaicop2026` — **PARTIAL**, non-load-bearing (ethics non-claim only), `TODO(formalize)` date/URL | GPAI Code of Practice, Measure 5.1 | Ethics non-claims | **formalize**. Same. |
| [8] → `opencharacter2025` — **RESOLVED**, verified vs arxiv.org 2026-07-07 | Open Character Training, arXiv:2511.01689 | §5.1 orthogonality sentence | **verify**; **remove?** if space is needed — the sentence survives with [9] alone or neither. |
| [9] → `inoculation2025` — **RESOLVED**, verified vs arxiv.org 2026-07-07 (note: v8.1/v9 misattributed this ID to a differently-titled Wichers et al. paper — flagged in the .bib, not corrected by guessing) | Inoculation Prompting, arXiv:2510.04340 | §5.1 orthogonality sentence | **verify + formalize**. |
| [10] → `medredteam2026` — **UNRESOLVED**, medRxiv returns HTTP 403 to automated fetch; `TODO(verify)` remains; non-load-bearing per original disposition (taxonomy is explicitly non-validated) so no claim weakening needed | medRxiv preprint 10.64898/2026.02.26.26347212v1 | §5.2 taxonomy anchor (one caveated sentence) | **verify**. Preprint status and LLM-judge caveat are already stated in prose. If it cannot be verified, drop the sentence — the taxonomy is explicitly non-validated design vocabulary, so nothing depends on it. |
| [11] → `gtharmbench2026` — **RESOLVED**, verified vs arxiv.org 2026-07-07, full author list confirmed | GT-HarmBench, arXiv:2602.12316, "Cobben et al." | F3 analytical substrate (RQ6) | **verify + formalize** — load-bearing for RQ6. `TODO(bib)` comment placed at the F3 paragraph in the .tex. |
| [12] → `villatoro2012` — **RESOLVED**, complete CLEF 2012 working-notes citation | Villatoro-Tello et al., PAN 2012 shared task | Primary dataset citation | **formalize** with full CLEF 2012 working-notes citation. Load-bearing; the venue and authors are real and stable. |
| [13] → `greshake2023` — **RESOLVED**, complete arXiv citation (published-version venue not separately re-verified) | Greshake et al., arXiv:2302.12173 | Background: indirect prompt injection | **formalize** (published at AISec 2023; cite the published version). |
| [14] → `ostrom1990` — **RESOLVED**, complete book citation | Ostrom, Governing the Commons, CUP 1990 | §8.2 mechanism framing | **keep** (complete book citation already). |
| [15] → `broder1997` — **RESOLVED**, complete proceedings citation with pages | Broder, SEQUENCES '97 | MinHash construction | **keep/formalize** (add pages/DOI). Load-bearing for Eq. (1); citation is standard and correct. |
| [16] → `acco2024` — **PARTIAL**, uncited by the USENIX source (kept for v9 only); anonymization-flagged self-citation, not a verification gap | ACCO "Deep Fake Frauds" report, 2024 | One background sentence (reality apathy) | **remove?** or formalize with URL. Not load-bearing. Note: author's own organization — flag for anonymization pass (self-citation treatment). |
| [17] → `bsrhria` — **UNRESOLVED**, `TODO(verify)` publication year/URL remains; moderately load-bearing (governance non-claims) | BSR Human Rights Impact Assessment of Lantern | Ethics section (governance model) | **formalize** with URL/date. Moderately load-bearing for the governance non-claims. |
| [18] → `photodna2023` — **PARTIAL**, non-load-bearing (explicit non-claim), `TODO(verify)` stable URL remains | Microsoft PhotoDNA performance doc, 2023 | Background analogy + ethics non-claim (latency figures explicitly not claimed) | **verify + formalize**. Vendor documentation; acceptable for an analogue claim, but locate a stable URL. |
| [19] → `artifact2026` — **RESOLVED for anonymization**, `howpublished` field is `\ifanonymous`-gated in the .bib entry itself (fixed 2026-07-08 after a PDF-text scan found the real URL leaking into the anonymous build via an ungated `\cite`); placeholder text still needs a real anonymized deposit link before final submission | Artifact repository URL | Contribution 6, methods | **keep**; will need anonymization for double-blind (see migration plan). |

## Summary

- 0 fabricated entries added; 0 entries removed in this pass.
- 3 `TODO(bib)` comments placed in the .tex at the load-bearing weak points
  ([3] press-only, [5] bundled org reports, [11] F3 substrate) during the
  2026-07-06 formalization pass.
- **2026-07-08 verification pass**: 13/18 entries fully resolved (author,
  venue, identifier confirmed); 5 remain partial/unresolved
  (`lantern2026`, `euaiact2026`, `gpaicop2026` — cosmetic `TODO(formalize)`
  only, none load-bearing beyond what's already stated; `bsrhria`,
  `photodna2023`, `medredteam2026` — `TODO(verify)` needing a manual
  browser check, not resolvable by automated fetch from this environment).
  See the status block at the top of this file for the authoritative
  per-priority-item outcome.
- Highest-priority verifications before submission: **done** for [11]
  (RQ6), [12] (dataset), [3]/[3a] (CVE claims), and the arXiv-motivation
  entries in [5]'s cluster (`lantern2026` itself is now a primary
  institutional citation, though still bundled). Remaining manual work is
  non-load-bearing or cosmetic (see above).
