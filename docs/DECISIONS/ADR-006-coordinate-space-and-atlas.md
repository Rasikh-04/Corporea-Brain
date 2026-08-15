# ADR-006 — Canonical coordinate space and parcellation atlas

**Status:** Open — **BLOCKING**
**Date raised:** 2026-08-15
**Owner:** Imaging
**Deadline:** Before any pipeline code is written
**Blocks:** The entire imaging pipeline, region attribution, the atlas layer, the data model's geometric fields

## Context

This is the most consequential open decision in the project and the one most likely to be
deferred because it feels like detail. It is not detail.

Every dataset in use arrives in a different orientation and resolution. Attribution requires
that a lesion mask and a parcellation live in the same space, on the same grid, with the same
handedness. Get this wrong and the lesion lands in the wrong lobe, every downstream output is
confidently incorrect, and **nothing in the software will warn you** — the images will look
entirely normal.

Two questions must be answered together, because they interact.

**Question 1: which canonical space?**

| Option | Pros | Cons |
|---|---|---|
| Template space, e.g. MNI152 | One space for attribution; atlas labels are native to it; group comparison possible | **Normalisation assumptions break with a large mass lesion.** Registration converges anyway and is wrong precisely where it matters |
| Subject-native space | No normalisation distortion; what the clinician sees is what was measured | Atlas labels must be warped to the subject, which moves the same error to a different step rather than removing it |
| **Both, with a declared direction** | Attribution computed in one space, displayed in the other, with transforms stored as artifacts | More plumbing; the direction must be declared once and never varied |

**Question 2: which parcellation?**

| Atlas | Granularity | Clinical interpretability | Licensing |
|---|---|---|---|
| Desikan-Killiany | Coarse, ~68 cortical | **High.** Names clinicians recognise | Via FreeSurfer, verify |
| Destrieux | Finer, ~148 | Moderate | Via FreeSurfer, verify |
| Harvard-Oxford | Probabilistic | High | Verify |
| AAL3 | Moderate | Moderate | Verify |
| Schaefer | Functional parcels, configurable | **Low for this use.** Functional parcels are not what a radiology report names | Verify |
| JHU white matter | Tracts | High for tract involvement | Verify |

## Recommendation, pending the exercise below

- **Compute attribution in the space where the parcellation is defined, and store forward and
  inverse transforms so results are displayed in subject-native space.** The clinician looks at
  the patient's own anatomy; the arithmetic happens where the labels are.
- **Desikan-Killiany as the default cortical parcellation**, plus subcortical segmentation, plus
  the JHU white matter atlas for tracts. Chosen for interpretability: agreement against a
  radiology report is easier to defend when the atlas uses the names the report uses.
- Support a second parcellation through the organ manifest's `parcellations[]` list, so the
  choice is configuration rather than an assumption baked into code.

## What is needed to close this

**Do the orientation exercise first. It is not optional and it is not busywork.**

1. Take one real DICOM study. Convert it. Inspect the affine.
2. Load it in three independent tools and confirm left is left in all three. **Write down how
   you verified it.**
3. Deliberately break the orientation and observe how invisible the failure is.
4. Build the synthetic asymmetric phantom and the assertion, and make it a CI test before any
   pipeline stage exists.
5. Verify the licensing of each candidate atlas and record it in the licence register.
6. Confirm with the clinician which region naming they actually use in reports. This decides
   the region category set for E2 agreement scoring, and that set must be fixed before any
   scoring happens.

## Consequences of leaving it open

Nothing in [`../06-IMAGING_PIPELINE.md`](../06-IMAGING_PIPELINE.md) can be implemented
correctly. Every geometric field in [`../05-DATA_MODEL.md`](../05-DATA_MODEL.md) has an
unresolved `coordinate_space`. The organ manifest's `parcellations[]` cannot be validated.
`RegionAttribution` — the core contribution — cannot be written.

**This is the single highest-priority open item in the project.**
