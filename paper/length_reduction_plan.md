# Length reduction plan — applied in the USENIX-oriented source

Source: `paper/usenix/adversarial_intent_telemetry_usenix.tex` (9 two-column
pages incl.\ references and artifact appendix, under the fallback
USENIX-geometry preamble). The 27-page single-column v9 draft
(`Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.tex`) remains the
long-form record; nothing was deleted from it. All cuts below are cuts in
the USENIX source only, and every cut item survives either in the v9 draft
or in the artifact.

## Cuts applied (v9 → USENIX)

| v9 material | Disposition in USENIX source | Where it lives now |
|---|---|---|
| Feature-manifest appendix (2.5 pp longtable) | **Cut**; one-sentence pointer | `spec/manifest-schema.json`, v8.1 design doc, v9 draft appendix |
| Handshake Algorithm 1 + JSON wire listing (~1.5 pp) | **Cut**; summarized in one sentence (match → human investigation; schema-level privacy invariant) | v9 draft §5.4, design doc |
| Six-class taxonomy table (~1 p) | **Compressed** to a one-sentence class list, explicitly design vocabulary | v9 draft §5.2 |
| LSH derivation (2 numbered eqs + prose) | **Compressed**: Eq. (1) kept; FPR bound stated inline; PSI/homomorphic options dropped | v9 draft §5.4 |
| Synthetic S-curve section + table | **Compressed** to three sentences inside Design Under Test (keeps the 0.085-recall foreshadowing) | v9 draft §5.6, `validation/synthetic/` |
| Threat model (assets, A1–A5, goals, out-of-scope; ~2 pp) | **Compressed** to one paragraph each, all five classes and the A2 non-validation caveat retained | v9 draft §4 |
| Evidence & Validity Matrix (longtable, 11 rows) | **Converted** to a `table*` `tabular`, same 11 rows, cells tightened | — |
| Two separate sweep tables | **Merged** into one generated table (`tab_perturbation_sweeps_merged.tex`, both splits side by side) | individual tables still generated for the v9 draft |
| Sweep + FP-substrate + author-disjoint figures | **Cut** (frontier and controls figures kept); tables carry the numbers | `experiments/results/*.pdf` |
| Background CVE inventory + reality-apathy paragraph | **Compressed** to one sentence of citations | v9 draft §3 |
| Repeated caveats (family-limited, corpus-vintage, split notes) | Stated once in Results/Limitations instead of per-section | — |
| Governance/latency non-claims | Folded into Ethics and Safety §8, kept as explicit non-claims | v9 draft §9 |
| RQ4 narrative (three-stage) | Tightened ~40%, all numbers and both negative attributions retained | v9 draft |

## Kept in full (per instructions)

Evidence & Validity Matrix (compressed, not cut); MinHash negative result +
frontier table + figure; clean trajectory negative result with CI;
author-disjoint replication; aggregation/order-control finding with the
controls table; paired statistical comparison table; Ethics and Safety
(standalone §8); Open Science (standalone §9); Limitations (all six items).

## Headroom

At 9 pages under the fallback preamble, the draft has ~4 pages of headroom
against a typical 13-page USENIX body limit. The official style file will
change lengths slightly (section fonts, caption spacing); re-measure after
dropping it in. If more space is ever needed, candidates to *restore* (in
order): the sweep dose-response figure (`figure*`), the synthetic S-curve
table, a compact version of the manifest schema.
