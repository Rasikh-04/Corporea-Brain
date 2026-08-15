# 03 — Architecture

**Decided shell:** a custom 3D Slicer application built with SlicerCustomAppTemplate.
Rationale and alternatives in [ADR-003](DECISIONS/ADR-003-application-shell.md).

<a id="layers"></a>

## Layer diagram

```
┌──────────────────────────────────────────────────────────────┐
│  APPLICATION SHELL                                           │
│  Branding, layout, home module, startup disclaimer,          │
│  curated module set, UI bundle loader                        │
├──────────────────────────────────────────────────────────────┤
│  BODY LAYER                                                  │
│   • Organ registry (manifest-driven)                         │
│   • Body-level navigation: pick an organ, enter its module   │
│   • Shared: patient record, timeline, provenance, export     │
├──────────────────────────────────────────────────────────────┤
│  ORGAN MODULES  (one interface, three depths)                │
│   ┌───────────────┬──────────────┬─────────────────────────┐ │
│   │ BRAIN  (deep) │ EAR (shallow)│ OTHER ORGANS (stub)     │ │
│   │ atlas+labels  │ atlas+labels │ atlas mesh + label only │ │
│   │ segmentation  │ disorder map │ "not implemented" state │ │
│   │ attribution   │              │                         │ │
│   │ deficits      │              │                         │ │
│   │ navigation    │              │                         │ │
│   └───────────────┴──────────────┴─────────────────────────┘ │
├──────────────────────────────────────────────────────────────┤
│  CORE SERVICES                                               │
│   Ingest · Preprocess · Registration · Segmentation ·        │
│   Atlas/parcellation · Record store · Provenance · Eval      │
├──────────────────────────────────────────────────────────────┤
│  PLATFORM  (Slicer core: MRML scene, VTK render, ITK, CTK,   │
│  DICOM database, Qt UI, Python, extension manager)           │
└──────────────────────────────────────────────────────────────┘
```

The critical structural decision: **the record store, timeline and provenance live at the
body layer, not inside the brain module.** That is the piece no competitor has, and burying
it inside an organ would make it un-reusable and would weaken the architectural claim.

<a id="platform"></a>

## Platform layer

3D Slicer is a Qt/C++ application built on VTK, ITK, CTK, CMake and Python, with a lean
application core plus modules providing functionality. We do not fork it and we do not patch
it. We configure it.

What the platform supplies, that we therefore do not build:

| Supplied | What it replaces in our plan |
|---|---|
| DICOM import, local database, series handling | The hardest part of R0 |
| Segment Editor, manual and semi-automatic tools | Months |
| Registration: rigid, affine, deformable via ITK, Elastix, ANTs modules | Months |
| GPU volume rendering, multi-planar reconstruction, 3D views, transfer functions | The whole R1 and R4 rendering layer |
| Markups: fiducials, lines, rulers, angles | R3 primitives |
| MRML scene serialisation, undo, extension manager, Python console | Infrastructure we would never finish |
| Cross-platform build and installer generation | Weeks of packaging work |
| A module architecture that *is* the organ plugin system | The R1 modularity claim, made real |

**Honest cost.** The superbuild compiles its own dependency tree; first successful build on a
new machine is realistically a day or two and wants substantial disk and RAM. We inherit a
large codebase and must learn MRML, module types and Slicer conventions. Both are addressed
in [`15-BUILD_AND_ENVIRONMENT.md`](15-BUILD_AND_ENVIRONMENT.md).

<a id="shell"></a>

## Application shell

Produced by setting CMake variables in the custom-app template, not by editing Slicer source:
application name, organisation, startup disclaimer, default home module, default favourite
modules, and which built-in modules are removed from the curated set.

Shell responsibilities:

1. Show the non-clinical-use disclaimer at startup, before any data is loaded. Text in
   [`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md).
2. Set the home module to the Body Layer, not to a Slicer module.
3. Load the active UI bundle. See [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md).
4. Hide the full Slicer module list behind an explicit "advanced" affordance. A clinician
   should never meet the researcher toolkit by accident, and the trainee should be able to.
5. Initialise the audit log and the record store before any module can write.

<a id="body-layer"></a>

## Body layer

Three components, all organ-agnostic.

- **OrganRegistry.** Discovers organ manifests at startup, validates them against the schema
  in [`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md), and exposes the list with
  implementation levels. A manifest that fails validation is reported, never silently skipped.
- **BodyNavigator.** The entry screen. A navigable shell model, organ picker, implementation
  level badges (deep, shallow, stub). Selecting an organ hands off to its module.
- **PatientContext.** The currently open patient, study set and timeline. Organ modules read
  it; they do not own it. This is what makes an organ module replaceable.

<a id="core-services"></a>

## Core services

| Service | Responsibility | Type |
|---|---|---|
| `Ingest` | DICOM folder to study/series tree, sequence classification, conversion, BIDS layout, de-identification, QC report | Scripted, then C++ for the classifier if profiling demands |
| `Preprocess` | Reorientation, resampling, bias correction, skull stripping, co-registration, template registration. Idempotent, cached, resumable | Scripted + CLI wrappers |
| `Segmentation` | Model invocation and mask production. Owns no model weights in-tree | Scripted + CLI |
| `AtlasService` | Parcellation load, label lookup, region geometry, tract atlas | C++ loadable (hot path) |
| `Attribution` | Lesion mask intersected with parcellation, ranked involvement, uncertainty | C++ loadable (hot path) |
| `RecordStore` | Patient, observations, scores, relatives, timeline. See [`05-DATA_MODEL.md`](05-DATA_MODEL.md) | C++ loadable + Python bindings |
| `Provenance` | Stamps every derived artifact with source, tool, version, parameters, timestamp | Cross-cutting, C++ |
| `Eval` | Metrics, results tables, batch runs. Built before the segmenter | Python, outside the app |

<a id="module-inventory"></a>

## Module inventory and ownership

Every one of these is original work. This table is the source for
[`CONTRIBUTIONS.md`](CONTRIBUTIONS.md).

| Module | Rung | Fidelity target | Notes |
|---|---|---|---|
| `Ingest` | R0 | F | Sequence classifier is the novel piece |
| `OrganRegistry` | R1 | F | Manifest-driven; makes the body claim structural |
| `BrainAtlas` | R1 | F | Hierarchical tree, bidirectional pick, layer toggles, gap notes |
| `LesionAnalysis` | R2 | V | Segmentation orchestration, volumetry, longitudinal delta |
| `RegionAttribution` | R2 | V | **The core contribution.** Ranked overlap with uncertainty |
| `DeficitHypotheses` | R2 | V | Region and tract to literature-referenced correlates, ranked |
| `ClinicalRecord` | R2 | F | Structured history, family history, genogram, scores |
| `Timeline` | R2 | F | Scans, scores, events, medications, volume trend on one axis |
| `TrajectoryPlanner` | R3 | F | Entry/target, probe-eye view, structures-along-path, proximity |
| `ImmersiveReview` | R4 | D | SlicerVirtualReality, or export to the web viewer |
| `TrackedPointer` | R5 | D | PLUS/OpenIGTLink, SlicerIGT pivot and landmark registration |
| `QCReport` | X | F | Per-case orientation, resolution, missing series, warnings |
| `TeachingMode` | X | F | Anonymised case library, guided walkthrough |

<a id="module-type"></a>

## Module type policy

Slicer offers scripted (Python), loadable (C++ with a Qt GUI) and CLI (standalone executable)
modules. The policy:

1. **Every module starts as a Python scripted module.** It is faster to write, faster to
   change, and the whole team can read it.
2. **Port to C++ only on measured evidence.** The trigger is a profiled hot path that breaks a
   stated NFR in [`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md). A preference for C++ is
   not a trigger. Record the measurement in the ADR that authorises the port.
3. **CLI modules for anything that must run headless or in batch** — the evaluation harness
   invokes these, and they are what the nightly jobs call.
4. **Do not mix.** A module is one type. A scripted module that shells out to a CLI module is
   fine; a half-ported module is not.

<a id="data-flow"></a>

## Data flow for one case

```
USB / CD  ──▶ Ingest ──▶ classified series ──▶ dcm2niix ──▶ BIDS tree
                 │                                              │
                 └──▶ QC report (orientation, resolution)       │
                                                                ▼
                                                          Preprocess
                                       (reorient, resample, N4, strip,
                                        co-register, register to template)
                                                                │
                       ┌────────────────────────────────────────┤
                       ▼                                        ▼
                 Parcellation                             Segmentation
              (FastSurfer / SynthSeg)                (nnU-Net / BraTS lineage)
                       │                                        │
                       └──────────────┬─────────────────────────┘
                                      ▼
                             RegionAttribution
                     (mask ∩ parcellation, ranked, uncertainty)
                                      │
                       ┌──────────────┼──────────────┐
                       ▼              ▼              ▼
              TractInvolvement  DeficitHypotheses  Timeline entry
                       │              │              │
                       └──────────────┴──────────────┘
                                      ▼
                          Report export + provenance
```

Every arrow crosses a provenance boundary. Every node writes a `DerivedArtifact` row.

<a id="threading"></a>

## Threading and long-running work

The rules that keep the UI responsive and the results reproducible:

- **Nothing long-running on the main thread.** Segmentation, registration and parcellation run
  as CLI modules in a separate process, with progress reported back.
- **The MRML scene is touched only from the main thread.** Worker results are marshalled back
  before any node is created or modified. This is the single most common source of crashes in
  Slicer extension work.
- **Every long job is cancellable and resumable.** A cancelled job leaves the cache in a valid
  state and a resumed job does not recompute completed stages.
- **No job writes to the record store directly.** It produces artifacts; the orchestrating
  module commits them, once, with provenance.

<a id="extensions"></a>

## Extension dependencies

We depend on these; we do not vendor them.

| Extension | For | Rung |
|---|---|---|
| SlicerIGT | Pivot calibration, landmark registration | R5 |
| SlicerOpenIGTLink / PLUS Toolkit | Tracked pose streaming | R5 |
| SlicerVirtualReality | Immersive review (one of two options) | R4 |
| SlicerDMRI | Tract visualisation, if used | R2, R3 |
| SlicerElastix or ANTs modules | Deformable registration | R2 |

Each pinned to a version in [`15-BUILD_AND_ENVIRONMENT.md`](15-BUILD_AND_ENVIRONMENT.md).
An unpinned extension is a reproducibility failure.

<a id="upstream"></a>

## What we never modify upstream

We do not patch Slicer, VTK, ITK or CTK. If something upstream is wrong for us, the options
in order are: configure it, subclass it, wrap it, work around it in our own module, or file
it upstream and pin the workaround with a comment naming the issue. A local patch to a
superbuild dependency is unbuildable by the next person and unreproducible for the report.

<a id="seams"></a>

## Seams that must not be crossed

These are architectural invariants. A PR that violates one is rejected regardless of whether
it works.

1. **Organ modules never write to the record store directly.** They go through the body layer.
2. **The record store never imports an organ module.** Dependency points one way.
3. **UI bundles never contain logic.** Tokens, stylesheets and layout only. See
   [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md).
4. **The evaluation harness never imports the application.** It runs against CLI modules and
   file artifacts, so results can be reproduced without a GUI.
5. **No module hard-codes a parcellation, an atlas, or a coordinate space.** Those come from
   configuration resolved by ADR-006.
6. **No analysis logic exists in any exported viewer.** See
   [ADR-009](DECISIONS/ADR-009-web-poc-disposition.md).

<a id="deployment"></a>

## Deployment shape

One installer, one machine, no server, no network. The application, the curated module set,
the atlas assets, the model weights and the record store all live locally. Patient data never
leaves the machine by default. See [`17-RELEASE_AND_PACKAGING.md`](17-RELEASE_AND_PACKAGING.md)
and [`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md).

<a id="what-we-built"></a>

## How this survives "what did you actually build?"

An examiner will ask. The architecture is the answer, and it must be crisp:

> The platform is Slicer, as declared. Our contribution is the ingest sequence classifier,
> the region-attribution engine, the deficit-hypothesis layer, the longitudinal record
> module, the trajectory planner, and the evaluation harness. None of them exist in Slicer or
> any comparable free tool.

Maintain [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md) from day one, not from week thirty.

---

**Related:** [`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md) ·
[`05-DATA_MODEL.md`](05-DATA_MODEL.md) ·
[`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) ·
[ADR-003](DECISIONS/ADR-003-application-shell.md) ·
[build plan architecture](research/FYP_Brain_Digital_Twin_Build_Plan.md#architecture)
