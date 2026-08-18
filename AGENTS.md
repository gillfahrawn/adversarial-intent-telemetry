# AGENTS.md — Adversarial Intent Telemetry

Persistent context for agent sessions on this repository (Codex, Claude Code, or
any other coding agent). Read this file fully, then read `CLAUDE.md` fully,
before making any change to any file.

**`CLAUDE.md` and `README.md` are authoritative for current project framing.**
This file exists to carry agent-specific working constraints (tone, workflow,
quality checklist) that apply regardless of which agent is running. Where
anything below conflicts with `CLAUDE.md` or `README.md`, those two files win —
update this file to match them, not the other way around.

---

## 1. Project identity (do not drift from this)

This repository is an **empirical, mixed-result study**, not a protocol
announcement. It asks whether a cross-provider behavioral-signature detection
scheme — specified as a deployable protocol in
`Decentralized_Telemetry_Adversarial_AI_Intent_v8.1.pdf` — survives contact with
real adversarial data and adaptive perturbation. The paper is the **design under
test**. The repository reports what happened when its primitives were run
against real data (PAN 2012) and simulation/analytical substrates
(Byzantine/SPRT, GT-HarmBench).

The headline result is a decomposition, not a validation:
- Per-message LinearSVC detects grooming structure strongly on clean PAN 2012.
- The banded-MinHash signature primitive — the core cross-provider mechanism in
  the paper — fails to recall real conversations at any deployable FPR.
- The trajectory/sequence model does not beat the per-message baseline on clean
  data (negative F1 lift, CI excludes zero only on the negative side).
- Under adaptive/discourse perturbation, the per-message baseline degrades far
  more sharply than the trajectory model (in the heaviest perturbation set, it
  falls below random while the sequence model retains weak but real
  discrimination).
- Byzantine/reputation results are simulations of a mechanism under stated
  parameters, not deployment evidence.
- F3 reciprocity is an analytical mechanism-design result on GT-HarmBench game
  matrices, not a claim about LLM behavior.

**Never restate a design-paper claim (`specified`, `proposed`, `hypothesized`)
as if this repository demonstrated it.** Every claim in the README carries one of
the maturity tags in `CLAUDE.md` §5 (`real`, `simulation`, `analytical`,
`synthetic`, `negative`/`inconclusive`). When you add or edit a result, attach
the correct tag and do not upgrade it without new evidence committed to
`experiments/results/`.

**Temporal-domain mismatch**: PAN 2012 validates a 2012 human-grooming corpus,
not 2026 agentic automation. NCMEC/Lantern figures are sampling priors for
perturbation, never evidence of the 2026 attack distribution. State this
whenever a PAN 2012 or NCMEC-derived number is discussed.

---

## 2. Target audience

Primary: empirical AI-safety and adversarial-ML researchers who will clone the
repo and re-run the numbers. Secondary: T&S/detection engineers, AI-governance
staff, technically sophisticated hiring managers.

These readers trust epistemic modesty over confident claims and will notice
immediately if the README describes a result the corresponding result file
does not support, or a command that fails on a clean clone.

---

## 3. Repository state

**`CLAUDE.md` §3 is the single source of truth for what exists.** Check it
against the actual disk contents at the start of every session; if they
diverge, fix the table in `CLAUDE.md` before doing anything else. Do not
duplicate that table here — update `CLAUDE.md` instead.

**Hard rule**: never describe, link to, or give a command for a path that is
not listed as `exists` in `CLAUDE.md` §3.

---

## 4. Session workflow

1. Read `CLAUDE.md` fully, then this file.
2. Confirm `CLAUDE.md` §3 (Repository State) matches disk. Fix first if not.
3. Read the current `README.md` from disk, not from memory.
4. Identify what the user wants changed and which section(s) it affects.
5. Check `CLAUDE.md` §5 (claim discipline) for any rule bearing on the change.
6. Make the change.
7. Run the Quality Checklist (§5 below) before presenting the result.

When proposing README edits, show a diff or a clearly marked before/after
rather than the full file. When adding or editing an experiment script:
1. Verify it runs from a clean environment (no missing imports, no hardcoded
   absolute paths — outputs must be written relative to the script or repo
   root).
2. Confirm the output JSON is well-formed and lands in `experiments/results/`
   (or another path already documented in `CLAUDE.md` §3).
3. Update `CLAUDE.md` §3 with the new file before referencing it in the README.
4. Re-run `scripts/check_claims.py` if the change touches a number the README
   states.

---

## 5. Quality checklist

Run this before presenting any change to the user.

**Content accuracy**
- [ ] Every file path in the README exists and is marked `exists` in `CLAUDE.md` §3.
- [ ] No command in the README requires a path that is not on disk or not
      clearly marked as requiring restricted/gated data (PAN 2012, GT-HarmBench).
- [ ] Every result claim carries the correct maturity tag (`CLAUDE.md` §5) and
      matches the corresponding JSON in `experiments/results/`.
- [ ] `python scripts/check_claims.py` passes, or the drift is intentional and
      the README has been updated to match the JSON (never the reverse without
      new evidence).
- [ ] Negative/inconclusive results remain stated as negative/inconclusive —
      never smoothed into a positive framing.
- [ ] Temporal-domain mismatch (PAN 2012 vs. 2026 agentic threat) is not elided
      wherever a PAN 2012 number is used to support a broader claim.

**Tone and formatting**
- [ ] Measured, dry, precise register. Avoid *revolutionary*, *groundbreaking*,
      *state-of-the-art*, *comprehensive*, *robust* (as a filler adjective),
      *powerful*, and LLM-cadence filler ("It is worth noting…", "Crucially…").
- [ ] No emojis.
- [ ] Mermaid diagrams only (`flowchart`, `sequenceDiagram`, `stateDiagram-v2`);
      no raw HTML, no `classDef`/`style` directives, ≤12 nodes per diagram.

**Repository integrity**
- [ ] `CLAUDE.md` §3 matches actual disk contents.
- [ ] No absolute local paths (e.g. `/Users/...`) in committed result JSONs —
      use repo-relative paths.
- [ ] No new file referenced in the README before it exists on disk and is
      recorded in `CLAUDE.md` §3.

---

## 6. Data handling constraints

- Never generate, request, or reproduce explicit child sexual abuse content,
  grooming scripts, or operational abuse examples — this applies to code,
  docstrings, comments, commit messages, and test fixtures alike.
- Raw PAN 2012 XML and the GT-HarmBench CSV are restricted/gated datasets and
  must never be committed or redistributed from this repository. See
  `data/README.md`, `data/pan12/README.md`, `data/gt_harmbench/README.md`.
- Before adding or editing anything under `data/`, check `docs/data_audit.md`
  for which tracked derived files contain structural features only vs. raw
  text, and do not widen exposure of raw conversation text.

---

*Update this file only when an agent-workflow constraint changes. Project
framing, results, and repository state live in `CLAUDE.md` and `README.md` —
edit those first, then bring this file in line with them.*
