# 19 — Research bridge

**The connective document.** Short by design. Its only job is to make sure nothing that gets
built is orphaned from the thesis, and nothing the thesis claims is unbuilt.

<a id="sources"></a>

## The two source documents

Both are mirrored in [`research/`](research/) so the cross-links resolve locally.

| Document | Decides | Read it for |
|---|---|---|
| [Research plan](research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md) | **What is true and what is worth doing** | The landscape audit, the four surviving gaps, the scored thesis choice, the requirements skeleton, the learning tracks, the evaluation claims, the risk register |
| [Build plan](research/FYP_Brain_Digital_Twin_Build_Plan.md) | **What gets constructed, and in what order** | The six-rung ladder, the stack decision, the fidelity tiers, the timeline and gates, the twelve-minute demo script, the rung-to-chapter mapping |

**This documentation set is the third document, and it decides how it gets built.** Research
plan → build plan → this set. Each constrains the next, and none of them repeats the others.

<a id="rule"></a>

## The one governing rule

> Every rung of the ladder must emit at least one number that lands in a results table.

This is the hinge between the three documents. The research plan says which claims are worth
making; the build plan assigns each claim to a rung; this set specifies the artifact that
produces the number. A document here that does not eventually serve a number is scaffolding,
and scaffolding gets built cheaply and late.

<a id="rung-map"></a>

## Rung to document map

| Rung | Number it emits | Specified in |
|---|---|---|
| **R0** Ingest and spine | Ingest success rate; sequence-classification accuracy across N heterogeneous studies from ≥3 sources; per-stage wall time | [`06`](06-IMAGING_PIPELINE.md) Stages 0 to 2 · [`07`](07-SRS.md) F1 · [`05`](05-DATA_MODEL.md) |
| **R1** Atlas and body shell | Count of uniquely labelled structures; render fps at target volume; organ count by implementation level | [`04`](04-ORGAN_MODULE_SPEC.md) · [`08`](08-UI_UX_SPEC.md) S3, S4 · [`11`](11-NFR_AND_BENCHMARK.md) |
| **R2** Mapping, disorders, record | **Dice, HD95, ASSD; region-attribution agreement; longitudinal change reliability** | [`06`](06-IMAGING_PIPELINE.md) Stages 3 to 12 · [`10`](10-EVALUATION_PROTOCOL.md) · [`05`](05-DATA_MODEL.md) · [`08`](08-UI_UX_SPEC.md) S5 to S7 |
| **R3** Virtual neuronavigation | Planning task time; proximity-warning agreement vs expert; traversed structures the reviewer had not noted | [`08`](08-UI_UX_SPEC.md) S8 · [`07`](07-SRS.md) F3 |
| **R4** VR and AR review | Comparative task performance, immersive vs desktop | [ADR-009](DECISIONS/ADR-009-web-poc-disposition.md) · [`03`](03-ARCHITECTURE.md) |
| **R5** Tracked hardware | Pivot calibration RMS; **FRE and TRE in millimetres**; latency, jitter, occlusion failure rate | [`21`](21-RISK_REGISTER.md) · build plan Rung 5 |
| **X** Cross-cutting | Offline pass or fail; installer size; reproducibility check | [`11`](11-NFR_AND_BENCHMARK.md) · [`16`](16-TESTING_STRATEGY.md) · [`17`](17-RELEASE_AND_PACKAGING.md) |

<a id="claim-map"></a>

## Document to claim map

Which document is responsible for making each research-plan evaluation claim provable.

| Claim | What it asserts | Owned by |
|---|---|---|
| **E1** | Segmentation comparable to published baselines | [`10`](10-EVALUATION_PROTOCOL.md) Tables 4.1 · [`06`](06-IMAGING_PIPELINE.md) Stage 9 |
| **E2** | Region attribution agrees with expert reading | [`10`](10-EVALUATION_PROTOCOL.md) attribution protocol · [`06`](06-IMAGING_PIPELINE.md) Stage 10 |
| **E3** | Change detection across timepoints is reliable | [`10`](10-EVALUATION_PROTOCOL.md) Table 4.3 · [`07`](07-SRS.md) F6 |
| **E4** | Runs within stated resource limits, offline | [`11`](11-NFR_AND_BENCHMARK.md) · [`16`](16-TESTING_STRATEGY.md) offline test |
| **E5** | Clinicians find the output usable and useful | [`10`](10-EVALUATION_PROTOCOL.md) rubric · [`08`](08-UI_UX_SPEC.md) |
| **E6** | The structured record is faster or more complete | [`10`](10-EVALUATION_PROTOCOL.md) · [`07`](07-SRS.md) F5 |
| **E7** | Performance holds on local retrospective cases | [`10`](10-EVALUATION_PROTOCOL.md) · [`13`](13-LEGAL_AND_ETHICS.md) ethics route |

**Note the property worth protecting: E1, E3 and E4 need no clinician and no patient data.** If
ethics, hospital access or clinician availability all fail, there is still a complete
evaluation chapter. No design change may break that.

<a id="chapter-map"></a>

## Document to chapter map

So that writing can start in week 3 rather than week 33.

| Thesis chapter | Drafted from |
|---|---|
| 1 Introduction, scope, twin tiers | [`01`](01-VISION_AND_SCOPE.md) · [`02`](02-NON_GOALS.md) |
| 2 Background and related work | Research plan Parts 2 and 3 · [`18`](18-POC_INHERITANCE.md) |
| 3 Requirements and design | [`07`](07-SRS.md) · [`03`](03-ARCHITECTURE.md) · [`04`](04-ORGAN_MODULE_SPEC.md) · [`08`](08-UI_UX_SPEC.md) |
| 3b Methods: data and pipeline | [`05`](05-DATA_MODEL.md) · [`06`](06-IMAGING_PIPELINE.md) |
| 4 **Results** | [`10`](10-EVALUATION_PROTOCOL.md) tables · [`11`](11-NFR_AND_BENCHMARK.md) |
| 5 Implementation | [`03`](03-ARCHITECTURE.md) · [`14`](14-CODING_STANDARDS.md) · [`15`](15-BUILD_AND_ENVIRONMENT.md) · [`17`](17-RELEASE_AND_PACKAGING.md) · [`CONTRIBUTIONS`](CONTRIBUTIONS.md) |
| 6 Ethics, limitations, future work | [`12`](12-SECURITY_PRIVACY_COMPLIANCE.md) · [`13`](13-LEGAL_AND_ETHICS.md) · [`02`](02-NON_GOALS.md) deferred items |
| Appendices | [`09`](09-UI_BUNDLE_SPEC.md) · [`16`](16-TESTING_STRATEGY.md) · [`20`](20-AI_WORKFLOW_AND_COST.md) · [`21`](21-RISK_REGISTER.md) |

The landscape review, competitor teardown, legal memo and evaluation protocol **are already
chapters**. Writing them is not a separate task from doing the work.

<a id="gates"></a>

## Gates and their evidence

A gate is passed by producing an artifact, not by asserting progress.

| Week | Gate | Evidence required |
|---|---|---|
| 2 | Scope confirmed, shell decided | [`01`](01-VISION_AND_SCOPE.md) written · [ADR-003](DECISIONS/ADR-003-application-shell.md) accepted · one Slicer superbuild compiling |
| 7 | A real study loads | Real DICOM imported, converted, **orientation verified three ways with the method written down** |
| 12 | Wireframes criticised, harness works | A clinician has said something critical about a screen · the harness computes Dice on a dummy pair and passes its known-answer test |
| **22** | **HARD GATE: R2** | **Real numbers in a results table for at least one disorder.** Not screenshots. Numbers. If unmet, cut R3 to R5 now. |
| 28 | Two disorders validated | Table 4.1 populated for stroke and glioma · E5 sessions scheduled |
| 31 | Hardware number or descoped | TRE in millimetres obtained, or R5 formally descoped per its kill criteria |
| 33 | Offline and packaged | Offline test passes on a clean machine · installer produced |
| 38 | Defensible | Demo rehearsed end to end at least three times · `CONTRIBUTIONS.md` complete |

**Weeks 13 to 22 are sacred.** R2 is the thesis. Nothing interrupts it: not the ear
application, not a VR idea, not a stack re-litigation.

<a id="disagreements"></a>

## Where the plans and this set disagree, and which wins

Recorded so the divergence is deliberate rather than a drift nobody noticed.

| Topic | The plans say | This set says | Which wins, and why |
|---|---|---|---|
| Application shell | The build plan recommends a custom Slicer app but proposes ADR-003 as a three-way spike to be scored | **Decided: custom Slicer app.** No spike | **This set.** The decision was taken; the spike would now only confirm it. The build plan's own prediction was that this option wins on everything except VR, and VR is handled by ADR-009. |
| Stack evidence | The benchmark repository reads as though three stacks were compared at Tier 1 | **Tier 1 was completed only for Rust.** The Qt decision rests on ecosystem convergence, Tier 0 and imaging ergonomics | **This set.** [`18`](18-POC_INHERITANCE.md) and [`11`](11-NFR_AND_BENCHMARK.md) state the gap explicitly. Overstating it is the easiest thing for an examiner to catch. |
| Web POC | The research plan leans web-first; the build plan resolves it as a thin VR viewer | **Retired as a product; optional thin viewer only, zero analysis logic** | **This set**, per [ADR-009](DECISIONS/ADR-009-web-poc-disposition.md). |
| Visual design | Neither plan addresses it | **Deferred behind a UI bundle seam**, with behaviour settled now | **This set**, per [ADR-008](DECISIONS/ADR-008-ui-bundle-seam.md). New material, not a contradiction. |
| Coordinate space and atlas | The research plan says pick, justify, document, be consistent | **Blocking open decision, ADR-006, before any pipeline code** | Consistent. This set raises it from advice to a gate. |
| Cognitive instrument | Both flag the MMSE licensing problem | **Enforced in the data model**: an instrument with no licence entry cannot be instantiated | **This set.** A policy that is only a policy gets broken at 2am. |

Where the plans and this set genuinely conflict on anything not listed above, **the plans win on
what is worth doing, and this set wins on how it is built.** If the conflict is about scope, the
plans win and this set is corrected.

<a id="sync"></a>

## Keeping the three in sync

- All three sets of documents live in this repository. That is what makes the cross-links work
  and it is why the plans are mirrored under [`research/`](research/) rather than linked
  externally.
- Both plans use explicit `<a id="…">` anchors so links survive heading edits. This set does the
  same. **Renaming a file means updating the links in the others**, and that is a pre-commit
  checklist item.
- The plans are at version 1 and are due revision after the first real build week. When they
  are revised, this section is the first thing to re-read.
- A change to scope updates [`01`](01-VISION_AND_SCOPE.md) and [`02`](02-NON_GOALS.md) **and**
  the plans. A change to how something is built updates only this set.

---

**Related:** [`00-INDEX.md`](00-INDEX.md) ·
[`01-VISION_AND_SCOPE.md`](01-VISION_AND_SCOPE.md) ·
[`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md) ·
[`CONTRIBUTIONS.md`](CONTRIBUTIONS.md)
