# 06 — Imaging pipeline

Every stage, the tool behind it, the coordinate space at each step, and the failure mode for
each. This is a first-class examinable artifact, not internal plumbing.

**Blocking dependency:** the canonical coordinate space and the parcellation atlas are
[ADR-006](DECISIONS/ADR-006-coordinate-space-and-atlas.md), still open. Nothing below can be
implemented correctly until it is closed. Placeholders read `<CANONICAL_SPACE>` and
`<PARCELLATION>`.

<a id="overview"></a>

## Pipeline overview

```
 0 Ingest & classify ──▶ 1 Convert & BIDS ──▶ 2 De-identify & deface
                                                        │
                                                        ▼
 3 Reorient & resample ──▶ 4 Bias field ──▶ 5 Skull strip ──▶ 6 Co-register
                                                        │
                                                        ▼
                                              7 Template registration
                                                        │
                              ┌─────────────────────────┴───────────────┐
                              ▼                                         ▼
                       8 Parcellation                          9 Lesion segmentation
                              │                                         │
                              └──────────────────┬──────────────────────┘
                                                 ▼
                                        10 Region attribution
                                                 │
                                    ┌────────────┴────────────┐
                                    ▼                         ▼
                          11 Tract involvement      12 Deficit hypotheses
```

Every stage is **idempotent, cached and resumable**, writes a `DerivedArtifact` with full
provenance, and contributes to the per-case QC report.

<a id="stage-0"></a>

## Stage 0 — Ingest and sequence classification

**In:** a DICOM folder from USB, CD or a local directory. **Out:** a study and series tree
with a classified sequence per series.

Classification is rules first, over `SeriesDescription`, `ScanningSequence`,
`SequenceVariant`, `ScanOptions`, `EchoTime`, `RepetitionTime`, `InversionTime`,
`ContrastBolusAgent` and `ImageType`. A small learned classifier is added **only** if the
rules demonstrably fail on the held-out study set, and its addition requires an ADR.

**Three safety rules, restated from the data model because this is where they are enforced:**

1. Always display the guess with its confidence. Never apply it silently.
2. Always allow a manual correction, and record that a correction happened.
3. Log every assignment with method and confidence.

**Number this stage emits:** ingest success rate and sequence-classification accuracy across
N heterogeneous studies from at least three sources; per-stage wall time.

**Failure modes:** vendor-specific private tags; a study with two series that both claim to be
T1; multi-echo series presented as one; localisers and scouts mistaken for diagnostic series;
secondary-capture screenshots of a report.

<a id="stage-1"></a>

## Stage 1 — Conversion and BIDS layout

`dcm2niix` to NIfTI, then a BIDS-compliant tree. BIDS is adopted from day one: it is free
credibility, free interoperability, and it forces the discipline the POC lacked.

**Failure modes:** dcm2niix emitting multiple files for one series; gantry-tilted CT
requiring correction; 4D series flattened incorrectly.

<a id="stage-2"></a>

## Stage 2 — De-identification and defacing

Header de-identification with a **verification test**, not an assumption. The test asserts
that no tag in the configured PHI set survives, and it runs in CI against a synthetic study
seeded with known PHI in every one of those tags.

**Defacing is required for T1 MRI.** A volume render of an un-defaced head is a photograph of
the patient. This is not optional and it is not a nice-to-have.

**Failure modes:** PHI burned into pixel data on secondary captures — header scrubbing does
nothing for it; PHI in `StudyDescription` and `SeriesDescription` free text; defacing that
removes anatomy the analysis needs.

<a id="stage-3"></a>

## Stage 3 — Reorientation and resampling

Reorient to `<CANONICAL_SPACE>` orientation. Resample to a declared isotropic grid. Record the
original orientation code and the affine before and after.

**This is where the project lives or dies.** See the orientation assertion below.

<a id="stage-4"></a>

## Stage 4 — Bias-field correction

N4 (ITK / ANTs). Skip for CT. Record whether it was applied and with which parameters.

**Failure mode:** aggressive correction flattening genuine lesion contrast, particularly at
the brain edge.

<a id="stage-5"></a>

## Stage 5 — Skull stripping

Learned or atlas-based, chosen with an ADR. Must be robust on clinical-quality scans, not only
on research-quality ones.

**Failure modes:** over-stripping cortex near a peripheral lesion, which then silently reduces
the measured lesion volume; under-stripping leaving dura that a segmenter reads as enhancement.

<a id="stage-6"></a>

## Stage 6 — Inter-series co-registration

Rigid, within-subject, all series to a chosen reference series. Report the residual.

**Failure mode:** registering to a series that is itself corrupt, propagating the error to
everything.

<a id="stage-7"></a>

## Stage 7 — Template registration

Subject to `<CANONICAL_SPACE>` template. Affine, then deformable, via ANTs or Elastix.
**Store the forward and inverse transforms as artifacts.** Attribution is computed in whichever
space ADR-006 selects; the transforms must exist to move results back to native space for
display.

**Failure mode, and it is the important one:** a large mass lesion breaks the assumptions of
normalisation. Registration will still produce a result; it will just be wrong, confidently.
See the mass-effect section below.

<a id="stage-8"></a>

## Stage 8 — Parcellation

FastSurfer for a FreeSurfer-conformant whole-brain segmentation; SynthSeg where the input is
off-protocol or low quality, which is the realistic clinical case. `<PARCELLATION>` supplies
the label set.

**Failure mode:** parcellating a brain with mass effect and reporting the labels as if the
anatomy were normal.

<a id="stage-9"></a>

## Stage 9 — Lesion segmentation

Fine-tuned nnU-Net or a pretrained BraTS-lineage model for glioma; a stroke lesion model
trained on ATLAS; ICH on CT if the third disorder is added.

**Fine-tune, do not invent.** A novel architecture adds nothing to this thesis and costs a
term. Report metrics immediately after each model lands — not at the end.

**Failure mode:** Dice is misleading for very small lesions. A small acute stroke can score
poorly while being localised perfectly. Report HD95 and ASSD alongside, and report per-size
strata. See [`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md).

<a id="stage-10"></a>

## Stage 10 — Region attribution

**This is the contribution.** Lesion mask intersected with the parcellation, producing a
ranked list of involved regions with, per region: overlap voxels, overlap as a fraction of the
region, overlap as a fraction of the lesion, rank, and an explicit uncertainty statement.

The uncertainty statement is not boilerplate. It names the specific error sources active for
that case: registration residual in millimetres, partial-volume effect at the given voxel
size, and mass-effect distortion where present.

**Rank, never filter.** Every region with non-zero overlap appears. The clinician's guidance
that missing is worse than over-flagging is honoured by ordering, not by suppressing the tail.

<a id="stage-11"></a>

## Stage 11 — Tract involvement

Lesion versus a white-matter atlas. We **consume** a tract atlas; we do not compute
tractography. If per-subject tractography is ever needed, SlicerDMRI does it and we would be
integrating, not implementing.

<a id="stage-12"></a>

## Stage 12 — Deficit hypotheses

A mapping table from region and tract to expected clinical correlates. Every entry carries a
literature citation and a confidence band. **Presented as hypotheses, never conclusions.**

The table is a reviewed data asset, not code. Entries with no citation carry the literal
`NEEDS_SOURCE` and block release. Handedness modulates language-lateralisation entries; where
handedness is unknown, the hypothesis is shown with an explicit caveat rather than assumed.

<a id="orientation"></a>

## The orientation assertion

Read this section twice. It describes the single failure mode most likely to invalidate the
entire project, and it is invisible when it happens.

A left/right flip anywhere in the chain produces a lesion in the wrong hemisphere. Every
downstream output — attribution, tract involvement, deficit hypotheses, the eloquent-proximity
warning — is then confidently, plausibly wrong. Nothing in the software warns you. The images
look fine.

**The control:**

1. A synthetic **asymmetric phantom volume** is committed to the repository. It has an
   unmistakable, deliberately lopsided marker.
2. The phantom is pushed through **every** stage that touches geometry, and a hard assertion
   verifies the marker is still on the expected side, with the expected voxel and world
   coordinates.
3. This runs as a **CI test**, on every commit, not as a manual check.
4. It runs again at application startup in a debug build, and the result is written to the log.
5. Every per-case QC report includes an orientation panel: the orientation code before and
   after, the affine determinant sign, and a rendered image with a laterality label burned in.

**Additionally, once, by hand, and written down:** take one real DICOM study, convert it, and
verify that left is left in three independent tools. Record how you verified it. Then
deliberately break the orientation and observe how invisible the failure is. Do this before
writing pipeline code, not after.

<a id="caching"></a>

## Caching, idempotence, resumability

- Every stage is keyed by a content hash of its inputs plus its parameters plus the tool
  version. Same inputs, same key, cached result reused.
- A stage never mutates its input. It writes a new artifact.
- A cancelled or crashed run leaves the cache valid; a resumed run recomputes only what is
  missing.
- Clearing the cache must be an explicit, single command, and it must not be able to delete
  source data.

<a id="qc"></a>

## Per-case QC report

Generated automatically, one per case, human-readable, and part of the demo.

Contents: orientation check (see above), voxel spacing and dimensions per series, missing
expected series, conversion warnings, registration residuals, skull-strip coverage sanity,
parcellation label count, per-stage wall time, and any stage that fell back to a default.

**A case with a failing QC panel cannot proceed to attribution without an explicit,
logged user override.**

<a id="failures"></a>

## Failure taxonomy

Every stage failure is classified, because "it broke" is not a result.

| Class | Meaning | Behaviour |
|---|---|---|
| `INPUT_INVALID` | The data cannot support this stage | Stop, report which input and why |
| `INSUFFICIENT_INPUT` | A required series is absent | Skip the dependent stages, record the reason, do not substitute a weaker proxy |
| `TOOL_FAILED` | External tool returned non-zero | Capture stderr, record the invocation, stop |
| `QC_FAILED` | Completed but a check did not pass | Continue only with a logged override |
| `DEGRADED` | Completed with a documented compromise | Continue, flag on every downstream output |

`INSUFFICIENT_INPUT` is borrowed directly from the EarTwin rule engine and it is the right
pattern: **a stage never substitutes a weaker proxy for a missing input.**

<a id="mass-effect"></a>

## Mass effect and the normalisation caveat

Registration to a template assumes the subject's anatomy is a plausible deformation of the
template. A large glioma with midline shift violates that assumption. The registration will
still converge. The parcellation will still produce labels. Both will be wrong near the lesion,
which is precisely where the answer matters.

**We do not hide this. We do three things:**

1. **Detect and quantify it.** Compute a midline shift estimate and a local Jacobian
   distortion measure near the lesion. Store both as measurements.
2. **Flag it on every downstream output** derived from a case above a declared threshold, with
   the measured value, not with a generic warning.
3. **Document it as a stated limitation** in the report, with the threshold and the evidence
   for it.

A well-documented limitation marks better than an undocumented good-looking result. This is
also the honest answer when an examiner asks what breaks.

---

**Related:** [`05-DATA_MODEL.md`](05-DATA_MODEL.md) ·
[`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md) ·
[`16-TESTING_STRATEGY.md`](16-TESTING_STRATEGY.md) ·
[ADR-006](DECISIONS/ADR-006-coordinate-space-and-atlas.md) ·
[research plan Hole 5](research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-5)
