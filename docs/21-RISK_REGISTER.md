# 21 — Risk register

<a id="how"></a>

## How to use this register

Reviewed at the weekly sync, every week, for fifteen minutes. Two questions per risk: has the
likelihood changed, and has the trigger fired.

**A risk with no named owner is not managed.** An empty owner cell is itself a finding.

Kill criteria are decided **now, while calm**, not in month seven while not calm. That is the
whole point of writing them down in advance.

<a id="technical"></a>

## Technical risks

| # | Risk | L | I | Mitigation | Trigger | Owner |
|---|---|---|---|---|---|---|
| B1 | Slicer superbuild fails or takes weeks | Med | High | Start it week 1 on the strongest machine. It is the first risk to retire, not the last | No successful build by end of week 2 | Build |
| B2 | Team stalls learning MRML and the module model | Med | High | Everyone does the Slicer tutorials in weeks 3 to 7, in parallel with R0. Prototype in Python | Nobody has a scripted module loading by week 7 | Lead |
| B3 | "What did you actually build?" at viva | High | High | The contribution sentence in the README now. `CONTRIBUTIONS.md` maintained from day one | Cannot state it from memory at any weekly sync | Lead |
| B4 | Ladder climbing beats depth: five shallow rungs, no numbers | High | **Critical** | The one-number-per-rung rule. The week-22 hard gate | Any rung started before its predecessor emitted a number | Lead |
| B5 | **Silent coordinate or orientation error corrupts all results** | Med | **Critical** | Orientation assertion as a CI test against a committed asymmetric phantom; QC panel per case; the manual three-tool verification, written down | Any geometry stage added without an assertion | Imaging |
| B6 | Sequence classifier mis-assigns silently | Med | High | Always display the guess; always allow correction; log every assignment | A classification path that does not surface its confidence | Ingest |
| B7 | Mass effect breaks normalisation and nobody notices | Med | High | Detect and quantify midline shift; flag every downstream output above threshold; document as a limitation | A large-lesion case processed without the flag appearing | Imaging |
| B8 | Atlas content authoring becomes a time sink | Med | Med | Link out to external references. Never author anatomy prose | Anyone writing structure descriptions for more than two days | Lead |
| B9 | Model weights carry a licence that forbids redistribution | Med | High | Every weight file gets its own licence register row before use | A weight added without a register entry | Governance |
| B10 | Two codebases both half-maintained | Med | Med | If a viewer exists it is thin, exported-to, zero analysis logic. Written into ADR-009 | Any analysis code appearing in a viewer | Lead |
| B11 | Slicer upstream revision drift breaks the build mid-project | Med | High | Pin the revision. Changing it is an ADR | An unpinned dependency discovered anywhere | Build |
| B12 | Performance regression hidden by cross-batch drift | Med | Med | Nightly jobs build baseline and HEAD in one batch and report ratios; absolutes only from an attended sitting | An absolute number quoted without a `batch_id` | Bench |
| B13 | A PHI leak through a log, a path or a test fixture | Med | **Critical** | PHI-in-logs assertion in CI against a seeded synthetic study; no source paths in logs | Any log line containing a path from a DICOM export | Governance |
| B14 | Encrypted store lost with the passphrase | Low | High | Stated at first run in plain language; documented as a limitation. No escrow, deliberately | — | Backend |

<a id="project"></a>

## Project risks

| # | Risk | L | I | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Local patient data or ethics approval never lands | High | Med | **Evaluation designed to complete on public data alone.** Local data is a bonus chapter, never a dependency | Data |
| R2 | Instructor changes direction again mid-project | High | High | Decision memo with written confirmation; ADRs record what was agreed and when | Lead |
| R3 | Team coordination fails over the break | High | High | Track ownership, one 45-minute weekly sync in a fixed slot, async-first, `HANDOFF.md` current | Lead |
| R4 | Scope creep back toward whole-body, simulation, or atlas | High | High | [`02-NON_GOALS.md`](02-NON_GOALS.md) read at every sync for the first month; every request tested against a user story | Lead |
| R5 | Segmentation underperforms and results look bad | Med | Med | Use pretrained and fine-tuned models, not novel architectures. **Report honestly with error analysis** — a well-analysed poor result marks better than an unexplained good one | ML |
| R6 | Ear workstream consumes brain capacity | High | High | Formal separation, [ADR-002](DECISIONS/ADR-002-brain-ear-split.md). Ear is shallow tier in the manifest, enforced by the organ contract | Lead |
| R7 | Writing left to the end | High | High | Chapters produced as phase deliverables from Phase 1. See [`19-RESEARCH_BRIDGE.md`](19-RESEARCH_BRIDGE.md) | Lead |
| R8 | Clinician becomes unavailable | Med | Med | Front-load the round-2 interview. Record everything. Build a second clinical contact | Clinical |
| R9 | Dataset agreement breached via a public repository | Med | High | `.gitignore` discipline, downloader scripts only, pre-publication audit before the repo goes public | Data |
| R10 | An unblocked ADR blocks everything downstream | High | High | ADR-006 is named as blocking with a deadline before any pipeline code | Lead |
| R11 | Budget or context exhaustion in AI-assisted work | Med | Med | Depth levels, the filter-before-escalate rule, phase-boundary compaction. See [`20`](20-AI_WORKFLOW_AND_COST.md) | Lead |
| R12 | Demo fails on the day | Med | High | Rehearse end to end at least three times on the actual machine. Pre-warmed caches in the demo build | Lead |

<a id="clinical"></a>

## Clinical and data risks

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| C1 | An over-confident output influences a real clinical decision | Low | **Critical** | Disclaimer at startup and persistently; hypotheses labelled as hypotheses; uncertainty on every value; no diagnosis claim anywhere |
| C2 | A finding is suppressed by a filter and missed | Low | **Critical** | Rank, never suppress. No filter control exists on the attribution list. Asserted by a UI test |
| C3 | A licensed instrument ships in the codebase | Med | High | Enforced in the data model: an instrument with no licence register entry cannot be instantiated |
| C4 | An un-defaced volume is rendered in 3D | Med | High | Defacing required, checked automatically and in the QC report; 3D render blocked without an override |
| C5 | Attribution is trusted at a granularity the atlas cannot support | Med | Med | Region category set fixed and declared before scoring; substitutions recorded and displayed |
| C6 | A `NEEDS_SOURCE` placeholder is filled with plausible text | Low | High | CLAUDE.md rule 2; schema check on citations; review checklist item |

<a id="kill"></a>

## Kill criteria summary

Decided in advance. When a criterion fires, descope calmly rather than negotiating.

| Rung | Kill criterion | Action |
|---|---|---|
| R0 | None. R0 is mandatory | If R0 is not solid, everything above it is built on sand |
| R1 | Anatomy content authoring runs past a few days | Stop authoring. Link out |
| R2 | **Two disorders not at Validated fidelity by the end of Phase 3** | **Cut R3 to R5 entirely and deepen R2.** One deeply validated capability beats five shallow ones, every time |
| R3 | R2 not Validated by the Phase 3 gate | Defer the whole rung |
| R4 | Not working within 2 engineer-weeks | Ship a recorded video and move on. VR is a showpiece, not a claim |
| R5 | Tracking not producing stable poses within 2 engineer-weeks | Drop to VR controllers, which need no calibration. If that also fails, ship as design plus simulation with tracking stubbed, and say so |

<a id="fallback"></a>

## The fallback scope

Decide this now so that if month six goes badly, descoping is calm rather than panicked.

**Minimum viable FYP, and it is still a good project:**

- R0 at Functional, R1 at Functional for brain only, **R2 at Validated for one disorder**,
  cross-cutting packaging.
- Body shell present with stubs. Ear shallow.
- No R3, R4 or R5. Each documented as designed-not-built, with the design included.
- One results chapter with real Dice, HD95 and ASSD numbers and a region-attribution agreement
  table.

That is complete, honest and defensible. Everything above it is upside.

**What is never acceptable:** all rungs at Demonstrator fidelity with no numbers anywhere. That
is a tech demo and it will be marked as one.

<a id="weekly"></a>

## Weekly review procedure

Fifteen minutes, fixed slot, written outcome.

1. Any trigger fired since last week?
2. Any likelihood or impact changed?
3. Any risk that has become a real problem — move it to the current work.
4. Any new risk discovered — add it with an owner before the meeting ends.
5. Read [`02-NON_GOALS.md`](02-NON_GOALS.md) aloud. First month only, then monthly.

---

**Related:** [`02-NON_GOALS.md`](02-NON_GOALS.md) ·
[`15-BUILD_AND_ENVIRONMENT.md`](15-BUILD_AND_ENVIRONMENT.md) ·
[`19-RESEARCH_BRIDGE.md`](19-RESEARCH_BRIDGE.md) ·
[research plan Part 10](research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-10)
