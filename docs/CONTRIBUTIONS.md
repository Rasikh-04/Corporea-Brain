# CONTRIBUTIONS

**Maintained from day one, not from week thirty.** This is the answer to the question an
examiner will certainly ask, and reconstructing it from memory at the end is a week of misery
that produces a worse answer.

Rule: **anything merged that is original work gets a row here in the same pull request.** A PR
that adds an original component and does not update this file is incomplete.

<a id="sentence"></a>

## The contribution sentence

> The platform is 3D Slicer, as declared. Our contribution is the ingest sequence classifier,
> the region-attribution engine, the deficit-hypothesis layer, the longitudinal neuro record
> module, the trajectory planner, and the evaluation harness — none of which exist in Slicer or
> any comparable free tool.

Every team member should be able to say this without looking.

<a id="modules"></a>

## Original modules

| Module | What it does that nothing else does | Rung | Status |
|---|---|---|---|
| `Ingest` | Sequence classification from tags and heuristics, with the guess always displayed, always correctable, and every assignment logged so classifier accuracy is measurable from real use | R0 | Not started |
| `OrganRegistry` | Manifest-driven organ discovery with declared implementation levels and machine-readable `known_gaps`. This is what makes the modularity claim structural | R1 | Not started |
| `BrainAtlas` | Bidirectional structure selection with per-layer gap declarations surfaced at the point of use | R1 | Not started |
| `LesionAnalysis` | Segmentation orchestration with volumetry, uncertainty bands and longitudinal delta | R2 | Not started |
| `RegionAttribution` | **The core contribution.** Ranked lesion-to-region attribution with per-region uncertainty statements naming the active error sources, and recorded substitutions where the atlas lacks geometry | R2 | Not started |
| `DeficitHypotheses` | Region and tract to literature-referenced clinical correlates, ranked never filtered, each carrying a citation and a confidence band, presented as hypotheses | R2 | Not started |
| `ClinicalRecord` | Structured longitudinal neuro record with handedness mandatory, family history and genogram, and licence-gated instruments | R2 | Not started |
| `Timeline` | Imaging quantification and clinical record on one axis. **Nothing else does this** | R2 | Not started |
| `TrajectoryPlanner` | Structures-along-path with entry and exit depths, plus ranked eloquent proximity | R3 | Not started |
| `QCReport` | Per-case quality control including the rendered orientation verification | X | Not started |

<a id="algorithms"></a>

## Original algorithms and methods

| Item | Why it is original | Status |
|---|---|---|
| Sequence classification rule set | Vendor-heterogeneous heuristics over DICOM tags, with measured accuracy reported as an R0 result | Not started |
| Ranked attribution with explicit uncertainty | The uncertainty statement names the specific active error sources per case — registration residual, partial volume, mass-effect distortion — rather than a generic caveat | Not started |
| Mass-effect detection and downstream flagging | Quantifies midline shift and local distortion, then flags every derived output above a declared threshold instead of silently reporting normal-anatomy labels | Not started |
| Substitution recording | When a site has no geometry in the atlas, the highlight is moved and the substitution is recorded and displayed, never silently approximated | Not started |
| The orientation assertion harness | A committed asymmetric phantom pushed through every geometry stage as a CI gate | Not started |

<a id="structures"></a>

## Original data structures

| Item | Specified in | Status |
|---|---|---|
| The organ manifest schema, including `known_gaps` and implementation levels | [`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md) | Specified |
| The longitudinal neuro record model, including genogram and licence-gated instruments | [`05-DATA_MODEL.md`](05-DATA_MODEL.md) | Specified |
| The `DerivedArtifact` provenance model, reproducible from rows alone | [`05-DATA_MODEL.md`](05-DATA_MODEL.md) | Specified |
| The `AttributionResult` shape with mandatory uncertainty | [`05-DATA_MODEL.md`](05-DATA_MODEL.md) | Specified |
| The pipeline failure taxonomy, including `INSUFFICIENT_INPUT` and `DEGRADED` | [`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) | Specified |
| The UI bundle seam: tokens, layouts, and the lint that enforces the accessibility floor | [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md) | Specified |

<a id="instruments"></a>

## Original evaluation instruments

| Item | Status |
|---|---|
| The evaluation harness: metrics, automatic results-table generation, version-stamped rows, known-answer tests | Not started |
| The region-attribution agreement protocol, including the declared category mapping, blinding, and inter-rater baseline | Specified |
| The expert usefulness rubric, six items | Specified |
| The offline verification test, packet-level | Specified |
| The application NFR benchmark, extending the inherited harness with quality metrics in the same row | Specified |

<a id="configured"></a>

## Configured, not built

Stated so the boundary is unambiguous and cannot be read as over-claiming.

| Item | What we did |
|---|---|
| The application shell | Set CMake variables in SlicerCustomAppTemplate: name, disclaimer, home module, curated module set |
| DICOM import and database | Used as supplied |
| Segment Editor | Used as supplied |
| Registration modules | Configured and invoked; parameters recorded in provenance |
| Volume rendering, MPR, 3D views | Used as supplied |
| Markups and fiducials | Used as supplied, as R3 primitives |
| Installer generation | Configured |

<a id="adopted"></a>

## Adopted unchanged

| Item | Role |
|---|---|
| 3D Slicer, VTK, ITK, CTK, Qt | The platform |
| nnU-Net, BraTS-lineage weights | Lesion segmentation. Fine-tuned, not invented |
| FastSurfer, SynthSeg | Parcellation |
| ANTs, Elastix | Registration |
| dcm2niix | Conversion |
| SlicerIGT, PLUS, OpenIGTLink | R5 tracking |
| Z-Anatomy derived meshes | Atlas geometry, with gaps declared |
| MNI152, the chosen parcellation, JHU white matter atlas | Reference spaces and label sets |

---

**Related:** [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md) ·
[`19-RESEARCH_BRIDGE.md`](19-RESEARCH_BRIDGE.md) ·
[`../README.md`](../README.md)
