# 22 — Glossary

So a document never has to define the same word twice, and so a new team member can read any
document in this set cold.

<a id="clinical"></a>

## Clinical terms

| Term | Meaning |
|---|---|
| **Ischemic stroke** | Brain injury from interrupted blood supply. One of the two disorders in scope. Named by the interviewed clinician as most common. |
| **Glioma** | A primary brain tumour arising from glial cells. The second disorder in scope. |
| **Intracerebral haemorrhage** | Bleeding within the brain. Deferred third disorder; CT is first-line. |
| **Eloquent area** | Cortex whose damage produces an obvious deficit — motor, sensory, language, visual. Volunteered by the clinician in the context of safer surgery. |
| **Handedness** | Right, left or ambidextrous. **Mandatory field.** It determines language lateralisation and therefore which regions are eloquent for a given patient. |
| **Anamnesis** | The patient's recounted history. |
| **Genogram** | A structured family diagram showing relationships and conditions across generations. |
| **Comorbidity** | A condition coexisting with the primary one. |
| **Mass effect** | Displacement of brain structures by a lesion. **Breaks the assumptions of template normalisation.** |
| **Midline shift** | Displacement of midline structures. The standard quantitative marker of mass effect. |
| **NIHSS, mRS, KPS, GCS** | Standardised clinical scales. Generally free to use; verify per jurisdiction. |
| **MMSE** | Mini-Mental State Examination. **Copyrighted and commercially licensed. Cannot ship.** |
| **MoCA** | Montreal Cognitive Assessment. Copyrighted, but with an academic permission path. |
| **SaMD** | Software as a Medical Device. What this would be if it claimed to influence a clinical decision. It does not. |

<a id="imaging"></a>

## Imaging terms

| Term | Meaning |
|---|---|
| **DICOM** | The medical imaging standard. Study contains series; series contain instances. |
| **NIfTI** | The neuroimaging volume format. Header carries the affine. |
| **BIDS** | Brain Imaging Data Structure. The community layout standard. Adopted from day one. |
| **Series description** | A free-text DICOM tag. **Notoriously inconsistent between scanners and sites**, which is why sequence classification is a real problem. |
| **T1, T1CE, T2, FLAIR, DWI, ADC, SWI** | MR sequences. Each shows something different, and stroke looks different at hour 3 than at week 3. |
| **Sequence classification** | Determining which series is which from tags and heuristics. R0's novel component. |
| **Parcellation** | Division of the brain into labelled regions by an atlas. |
| **Segmentation** | Delineation of a structure or lesion, producing a mask. |
| **Registration** | Aligning one image to another. Rigid, affine or deformable. |
| **Skull stripping** | Removing non-brain tissue. |
| **Bias field correction** | Removing low-frequency intensity non-uniformity. N4 is standard. |
| **Defacing** | Removing facial features from a head volume. **Required for T1 MRI**, because a 3D render is otherwise a photograph. |
| **Partial volume effect** | One voxel containing more than one tissue type. A named source of attribution uncertainty. |

<a id="coordinates"></a>

## Coordinate and space terms

| Term | Meaning |
|---|---|
| **RAS / LPS** | Anatomical axis conventions. Right-Anterior-Superior and Left-Posterior-Superior. **Mixing them is how left/right flips happen.** |
| **Affine** | The 4x4 matrix mapping voxel indices to world coordinates. |
| **Voxel vs world coordinates** | Index space vs physical space in millimetres. Never mixed in one field; the field name says which. |
| **MNI152** | A standard template space. |
| **Canonical space** | The declared reference space for this project. Pending [ADR-006](DECISIONS/ADR-006-coordinate-space-and-atlas.md). |
| **Subject-native space** | The patient's own image space. Used for display. |
| **Desikan-Killiany, Destrieux, AAL3, Harvard-Oxford, Schaefer** | Cortical parcellations, differing in granularity, licensing and clinical interpretability. |
| **JHU white matter atlas** | The tract atlas used for tract involvement. |
| **Orientation code** | A three-letter code such as `RAS` recording axis directions. Stored on every volume. |

<a id="platform"></a>

## Platform terms

| Term | Meaning |
|---|---|
| **3D Slicer** | The Qt/C++/VTK medical imaging platform this application is built on. |
| **SlicerCustomAppTemplate** | The wrapper for building a branded custom application without modifying Slicer source. |
| **MRML** | Medical Reality Markup Language. Slicer's scene and node model. **Touched only from the main thread.** |
| **Scripted / loadable / CLI module** | Slicer's three module types: Python, C++ with a Qt GUI, and standalone executable. |
| **VTK, ITK, CTK** | Visualisation, image processing and common toolkit libraries underneath Slicer. |
| **Superbuild** | A CMake build that compiles its own dependency tree. Slow, disk-hungry, and the first risk to retire. |
| **SlicerIGT, PLUS, OpenIGTLink** | Image-guided intervention extensions and the tracking transport. R5 only. |
| **UI bundle** | A packaged visual identity: tokens, stylesheet, layouts, icons, colormaps. Contains no logic. |
| **Organ manifest** | The declaration that makes an organ module discoverable and honest about its depth. |
| **known_gaps** | The manifest field recording what the geometry does not contain, and what that costs. |

<a id="project"></a>

## Project terms

| Term | Meaning |
|---|---|
| **R0 to R5** | The build plan's rungs. R2 is the thesis. |
| **Fidelity tier D / F / V** | Demonstrator, Functional, Validated. Never claim above the tier something was built at. |
| **E1 to E7** | The research plan's evaluation claims. E1, E3 and E4 need no clinician and no patient data. |
| **F1 to F9** | Functional requirement groups in the SRS. |
| **T1 / T2 / T3 twin** | Visualisation, quantitative and mechanistic digital twin tiers. We ship T2. |
| **`NEEDS_SOURCE`** | A literal placeholder for an uncited statement. Rendered visibly, never blank, never substituted. |
| **`TODO(neuro-review)`** | A marker for content awaiting clinical review. |
| **`INSUFFICIENT_INPUT`** | A stage or rule that cannot run because a required input is absent. **Never substitutes a weaker proxy.** |
| **`DEGRADED`** | Completed with a documented compromise. Flagged on every downstream output. |
| **Batch id** | The capture batch a benchmark number belongs to. **Numbers are comparable only within a batch.** |
| **Rank, never suppress** | The governing display rule, derived from the clinical guidance that missing is worse than over-flagging. |

<a id="metrics"></a>

## Metric definitions

| Metric | Definition | Watch out for |
|---|---|---|
| **Dice** | 2·\|A∩B\| / (\|A\|+\|B\|). Volumetric overlap | **Severely misleading for small lesions.** Always stratify by size |
| **HD95** | 95th percentile Hausdorff distance. Boundary agreement | Sensitive to one distant false-positive component |
| **ASSD** | Average symmetric surface distance | More stable than HD95, less intuitive. Report both |
| **Volume error** | Absolute and relative volume difference | Report as Bland-Altman, not as a mean |
| **Bland-Altman** | Agreement plot with bias and limits of agreement | A near-zero mean can hide large scatter |
| **Cohen's kappa** | Agreement beyond chance | Depends entirely on the category set. Fix and declare it first |
| **ICC** | Intraclass correlation. Agreement for continuous measures | State which form. Reviewers check |
| **FRE / TRE** | Fiducial and target registration error, in millimetres | TRE at points **not** used in registration is the meaningful one |
| **SUS** | System Usability Scale | Do not modify it, or it is comparable to nothing |
| **p95 / p99 frame time** | Percentile frame times | The percentiles, not the average, are what a user feels |

<a id="abbrev"></a>

## Abbreviations

ADR architecture decision record · ASSD average symmetric surface distance · BIDS brain imaging
data structure · CDSS clinical decision support system · CI continuous integration ·
DUA data use agreement · ERC ethics review committee · EW engineer-week · FRE fiducial
registration error · HD95 95th percentile Hausdorff distance · IQR interquartile range ·
MPR multi-planar reconstruction · MRML medical reality markup language · NFR non-functional
requirement · PACS picture archiving and communication system · PHI protected health
information · POC proof of concept · SaMD software as a medical device · SRS software
requirements specification · SUS system usability scale · TRE target registration error ·
VRAM video memory

---

**Related:** [`00-INDEX.md`](00-INDEX.md)
