# Expert-language and jargon audit — USENIX source

Audit of `paper/usenix/adversarial_intent_telemetry_usenix.tex`, read as a
skeptical systems/security reviewer (2026-07-08, Prompt 8). Each item records
the section, the original phrase, why it could bother an expert reviewer, the
replacement, and whether the change was applied. Em-dash removals are tracked
separately at the bottom; this section covers wording/terminology.

## Applied changes

| # | Section | Original | Why it bothers a reviewer | Replacement | Applied |
|---|---|---|---|---|---|
| 1 | Intro | "Several of its **load-bearing** claims do not survive." | "load-bearing" is a structural-engineering metaphor; used 3x in the paper it reads as a verbal tic rather than a precise term. | "Several of its **central** claims do not survive." | yes |
| 2 | Threat Model | "Out of scope ... and **load-bearing** for the ethics posture" | same metaphor, second occurrence. | "... and **central** to the ethics posture" | yes |
| 3 | Design Under Test | "treating the layer as **load-bearing**." | same metaphor, third occurrence; here it restates the design's own claim. | "treating that layer as the **structurally expensive** one to evade." | yes |
| 4 | Evidence table (row) | "Sequence model **degrades more gracefully** than per-message baseline" | "graceful degradation" is soft; a reviewer wants the measured quantity. The row is tied to AUC drops, but the claim wording should be precise. | "Sequence model **shows a smaller AUC drop** than per-message baseline" | yes |
| 5 | Methods (MinHash frontier) | "form the **federated** pool" | the paper does not implement federation; a single-process pooled signature set should not be called "federated". | "form the **shared reference** pool" | yes |
| 6 | Methods (MinHash frontier) | "This instantiates the design's **inline-match** primitive on real text." | "inline" implies inline/hot-path enforcement, which was never built or measured. | "This instantiates the design's **cross-provider match** primitive on real text." | yes |
| 7 | Evidence table caption + RQ6 intro | "**validate** mechanisms under stated parameters" | "validate" for a simulation/analytical result invites the objection that nothing was validated; the paper elsewhere is careful to say "not validated". | "**exercise** mechanisms under stated parameters" | yes |

## Considered and deliberately kept

- **"robust" / "robustness"** — kept. Every headline use is qualified in the
  same sentence or nearby ("under discourse-noise perturbation", "rests on the
  discourse-noise family", "rule-based families only"), and Limitations (2)
  states the ordering could reverse under adaptive attacks. The claim is not
  overstated.
- **"privacy invariant (no raw text or user identity in any payload)"** —
  kept. It is explicitly labelled design context ("retained in the design
  document ... not evaluated systems"); the paper never says
  "privacy-preserving" and claims no formal privacy property.
- **"federation detection lift"** (in the list of the design's five stated
  goals) — kept. It names a goal *of the design under test*, not a property
  this paper implemented; the surrounding text says the paper measures only
  primitives relevant to detection lift.
- **"agentic automation" (A2)** — kept everywhere. Every occurrence is either
  a negative ("not evidence about agentic automation", "not validated") or
  clearly marked as a design target, never as demonstrated by PAN 2012.
- **"Cryptographic hashes have zero tolerance for input drift"** — kept;
  correct usage (contrasting exact cryptographic hashing with LSH). No hash is
  called a cipher and no encryption is called a hash anywhere in the source.
- **"statistically resolved against every per-message comparison"** — kept;
  it is backed by the paired-bootstrap CIs in Table~\ref{tab:paired} (CIs
  exclude zero). Not a bare descriptive-difference significance claim.
- **"proof" / "prove" / "causal"** — none present; no change needed.
- **"deployment"** — every use is a *non-claim* ("supports no deployment
  claim", "any deployment claim would need ...", "review-queue prioritizer,
  not an enforcement trigger"). No implied production deployment.

## Em-dash removal (Task 2)

All em-dashes in rendered prose were removed and replaced with a colon,
comma, semicolon, parentheses, or a sentence break, chosen for natural
reading. Parenthetical em-dash pairs (which also read as AI-generated
caveat pile-ups, per Task 3/5) were converted to commas or parentheses, and
two sentences were lightly restructured (RQ4 subsection title; the
Conclusion's "open questions" sentence) to avoid a forced colon or an
over-long parenthetical.

Intentionally retained `---` occurrences: two LaTeX *comment* lines
(`% ---- Fallback ...`, `% --- Anonymization switch ...`) that are decorative
separators in the source and never render in the PDF. No `---` remains in any
rendered text; verified by post-edit grep and by a rendered-PDF text scan.
