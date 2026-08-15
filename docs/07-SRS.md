# 07 — Software requirements specification

<a id="purpose"></a>

## Purpose and audience

This is the requirement spine. It is written so that every requirement can be tested and every
requirement traces to a user story, a rung, and an evaluation claim. Requirements that fail
that trace are deleted, not weakened.

**Style rule.** Bad: "The system shall accurately segment lesions." Good: "For the held-out
test split of ATLAS v2.0, the system shall achieve a median Dice ≥ 0.65 and shall report
per-case Dice, HD95 and ASSD."

<a id="users"></a>

## Users and moments

See [`01-VISION_AND_SCOPE.md`](01-VISION_AND_SCOPE.md). Primary user is pending
[ADR-004](DECISIONS/ADR-004-primary-user.md); the stories below assume neurologist primary and
trainee secondary, and are marked where the assumption matters.

<a id="stories"></a>

## User stories

Form: *As a [user], at [moment], I need [capability], so that [decision] changes.*

| # | Story | Serves |
|---|---|---|
| US-01 | As a **neurologist**, at a **follow-up consult**, I need to see how lesion volume and affected regions changed since the last scan, so that I can decide whether current management is working. | F3, F6 |
| US-02 | As a **neurologist**, at **first presentation**, I need to capture structured history including handedness, comorbidities, family history and obstetric history in under three minutes, so that the record is complete and reusable at every later visit. | F5 |
| US-03 | As a **neurosurgeon**, at **pre-operative review**, I need to see which eloquent regions and white-matter tracts the lesion abuts, with a stated confidence, so that I can factor risk into the approach discussion. | F3, R3 |
| US-04 | As a **neurologist**, at **any visit**, I need to administer and store a cognitive screening instrument and see the score trend, so that I can detect decline objectively rather than by impression. | F5, F6 |
| US-05 | As a **clinician in a hospital without PACS**, I need to load a study from a CD or USB with no internet and no server, so that the tool is usable where I actually work. | F1, NFR-02 |
| US-06 | As a **resident**, at **study time**, I need to step through a real anonymised case from history to imaging to region attribution, so that I build clinical-anatomical correlation. | F9 |
| US-07 | As a **department**, at **audit time**, I need an exportable, provenance-stamped record of what the system computed and with which version, so that findings are reproducible. | F7, F8 |
| US-08 | As a **neuroradiologist**, at **reporting**, I need lesion volumetry and prior-versus-current comparison, so that I can state change quantitatively rather than as an impression. | F3, F6 |
| US-09 | As a **neurologist**, at **any moment**, I need to see which atlas and which coordinate space produced a label, so that I can judge whether to trust it. | F4, F8 |
| US-10 | As a **user of any kind**, I need the system to never hide a candidate finding, so that I make the decision about relevance rather than the software. | F8 |
| US-11 | As a **team member**, at **ingest**, I need to see and correct the system's guess at which series is which, so that a misclassification never propagates silently. | F1 |
| US-12 | As a **clinician**, at **case close**, I need a structured report I can print or attach to a paper file, so that the work survives outside the application. | F7 |

<a id="f1"></a>

## F1 — Ingestion

| # | Requirement | Fidelity | Test |
|---|---|---|---|
| F1.1 | Import a DICOM study from a local folder, USB or CD, producing a study and series tree. | F | Integration test on ≥3 studies from ≥3 different sources |
| F1.2 | Classify each series as T1, T1CE, T2, FLAIR, DWI, ADC, SWI, CT or UNKNOWN, and display the guess with a confidence value. | F | Classification accuracy measured on the study set |
| F1.3 | Allow the user to correct any classification, and record that a correction occurred. | F | UI test |
| F1.4 | Log every classification with method and confidence. | F | Log assertion |
| F1.5 | Convert to NIfTI and lay out in a BIDS-compliant tree. | F | Structure validation |
| F1.6 | De-identify DICOM headers and verify the result by test. | F | CI test with a synthetic PHI-seeded study |
| F1.7 | Deface T1 MRI volumes. | F | Visual and automated check |
| F1.8 | Import NIfTI directly, bypassing DICOM. | F | Unit test |
| F1.9 | Report ingest failures by class, per the failure taxonomy. | F | Unit test per class |

<a id="f2"></a>

## F2 — Preprocessing

| # | Requirement | Fidelity | Test |
|---|---|---|---|
| F2.1 | Reorient every volume to the canonical orientation and record before and after codes. | F | Orientation assertion test |
| F2.2 | Resample to a declared isotropic grid. | F | Unit test |
| F2.3 | Apply bias-field correction to MR volumes, recording parameters. | F | Provenance assertion |
| F2.4 | Skull strip, with a coverage sanity check in the QC report. | F | Golden-case regression |
| F2.5 | Co-register all series within a study to a reference series and report the residual. | F | Residual threshold assertion |
| F2.6 | Register to the template space and store forward and inverse transforms as artifacts. | F | Round-trip test |
| F2.7 | Be idempotent, cached and resumable at every stage. | F | Kill-and-resume test |
| F2.8 | Produce a per-case QC report including the orientation panel. | F | Snapshot test |

<a id="f3"></a>

## F3 — Analysis

| # | Requirement | Fidelity | Test |
|---|---|---|---|
| F3.1 | Segment ischemic stroke lesions. Median Dice ≥ 0.65 on the ATLAS v2.0 held-out split, with per-case Dice, HD95 and ASSD reported. | **V** | E1 |
| F3.2 | Segment glioma sub-regions. Performance reported against the current BraTS validation split with the standard sub-region breakdown. | **V** | E1 |
| F3.3 | Compute lesion volume per label in millilitres with an uncertainty band. | V | Bland-Altman against ground truth |
| F3.4 | Parcellate the brain using the configured atlas. | F | Label count assertion |
| F3.5 | Attribute the lesion to atlas regions, producing a ranked list with overlap voxels, overlap fraction of region, overlap fraction of lesion, and a non-empty uncertainty statement per region. | **V** | E2 |
| F3.6 | Never filter a region with non-zero overlap out of the attribution list. | V | Unit test asserting list completeness |
| F3.7 | Report white-matter tract involvement against the tract atlas. | F | Unit test |
| F3.8 | Produce ranked deficit hypotheses, each with a citation and a confidence band, labelled as hypotheses. | F | Schema test: no entry without a citation |
| F3.9 | Detect and quantify mass effect, and flag every downstream output from a case above the declared threshold. | F | Synthetic mass-effect case |
| F3.10 | Compare a study to a prior study of the same patient and report volume delta with uncertainty. | V | E3 |

<a id="f4"></a>

## F4 — Visualisation

| # | Requirement | Fidelity |
|---|---|---|
| F4.1 | 2D orthogonal views with overlay, window and level control. | F |
| F4.2 | 3D surface and volume rendering of the patient volume. | F |
| F4.3 | Region highlighting driven by the attribution result, bidirectional between mesh and list. | F |
| F4.4 | Side-by-side and difference views across two timepoints. | F |
| F4.5 | Persistent display of the active parcellation and coordinate space. | F |
| F4.6 | Perceptually uniform, colourblind-safe colormaps for all clinical overlays. | F |
| F4.7 | Layer toggles with the corresponding `known_gaps` note surfaced at the point of use. | F |

<a id="f5"></a>

## F5 — Clinical record

| # | Requirement | Fidelity |
|---|---|---|
| F5.1 | Capture demographics including **handedness as a required field**. | F |
| F5.2 | Warn explicitly if attribution is reached with handedness unknown. | F |
| F5.3 | Capture presenting complaint, examination findings, comorbidities, medications, allergies, addiction, occupation, marital status and obstetric history. | F |
| F5.4 | Capture family history and render a genogram. | F |
| F5.5 | Administer and store standardised scores with instrument version and licence reference. | F |
| F5.6 | Refuse to instantiate an instrument that has no licence entry. | F |
| F5.7 | Complete the core history in under three minutes for a target user. | F (measured, NFR-05) |

<a id="f6"></a>

## F6 — Timeline and comparison

| # | Requirement | Fidelity |
|---|---|---|
| F6.1 | Unified chronological view of scans, scores, events and medications on one axis. | F |
| F6.2 | Lesion volume trend plotted against the same axis. | F |
| F6.3 | Prior-versus-current comparison view launched from any two points. | F |
| F6.4 | Change detection flagged with its measured reliability, not as a binary. | V |

<a id="f7"></a>

## F7 — Reporting and export

| # | Requirement | Fidelity |
|---|---|---|
| F7.1 | Generate a structured PDF report containing findings, the attribution table, hypotheses with citations, uncertainty, provenance and the disclaimer. | F |
| F7.2 | Export measurements as CSV with units and provenance. | F |
| F7.3 | Export the full case record as JSON. | F |
| F7.4 | Every export carries application version, pipeline version and disclaimer. | F |
| F7.5 | Export a viewer scene containing geometry and labels only, with no analysis logic. | D |

<a id="f8"></a>

## F8 — Safety and governance

| # | Requirement | Fidelity |
|---|---|---|
| F8.1 | Display the non-clinical-use disclaimer at startup before any data is loaded. | F |
| F8.2 | Display uncertainty on every derived value. A value with no uncertainty is not rendered as a number. | F |
| F8.3 | Never suppress a candidate finding. Rank, never filter. | F |
| F8.4 | Maintain an append-only audit log covering writes and reads of identified fields. | F |
| F8.5 | Encrypt the record store and case directory at rest. | F |
| F8.6 | Make no outbound network connection by default. | F |
| F8.7 | Render `NEEDS_SOURCE` as a visible pending placeholder, never blank, never substituted. | F |

<a id="f9"></a>

## F9 — Teaching mode

| # | Requirement | Fidelity |
|---|---|---|
| F9.1 | An anonymised case library, separate from patient cases. | F |
| F9.2 | A guided walkthrough from history to imaging to attribution. | F |
| F9.3 | Anatomy reference layer with links out, never authored anatomy prose. | F |

<a id="nfr"></a>

## Non-functional requirements

Every value marked `<X>` is set from a measured baseline run, not guessed. See
[`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md).

| # | Requirement |
|---|---|
| NFR-01 | Full ingest to analysis to display for one MRI study completes in ≤ `<X>` minutes on the reference machine. |
| NFR-02 | **All core functions operate with the network interface disabled.** Verified by an explicit test that disables networking, not by inspection. |
| NFR-03 | Interactive 3D rendering sustains ≥ 30 fps average with p95 frame time < 33 ms at a declared volume size on the reference machine. |
| NFR-04 | Installer size ≤ `<X>` MB; peak RAM ≤ `<X>` GB; runs on integrated graphics with a documented degraded mode. |
| NFR-05 | A target user completes the defined core task after ≤ `<N>` minutes of instruction. Measured, per the clinician's comment that software familiarity takes weeks for the experienced. |
| NFR-06 | Identical input produces identical output. Every derived value carries tool version and parameters. |
| NFR-07 | The system never suppresses a candidate finding. The chosen operating point on the sensitivity-specificity curve is documented with its justification. |
| NFR-08 | Encryption at rest; no outbound transmission of patient data by default; de-identification verified by test. |
| NFR-09 | Cold start to usable UI ≤ `<X>` seconds on the reference machine. |
| NFR-10 | A crashed or cancelled pipeline run leaves the cache in a valid state and loses no completed stage. |
| NFR-11 | Every error surfaced to the user names the failure class and the specific input responsible. |
| NFR-12 | The application runs on Linux and Windows from the same source, with per-platform installers. |

<a id="traceability"></a>

## Traceability matrix

| Group | Stories | Rung | Evaluation claim | Chapter |
|---|---|---|---|---|
| F1 Ingestion | US-05, US-11 | R0 | E4, ingest rate | Methods: data and pipeline |
| F2 Preprocessing | US-05 | R0, R2 | E4 | Methods: pipeline |
| F3 Analysis | US-01, US-03, US-08 | R2 | **E1, E2, E3** | **Results, the core chapter** |
| F4 Visualisation | US-09 | R1, R2 | E4 render performance | Design and implementation |
| F5 Clinical record | US-02, US-04 | R2 | E6 | Design; Results secondary |
| F6 Timeline | US-01, US-04, US-08 | R2 | E3 | Results |
| F7 Reporting | US-07, US-12 | X | E4 | Implementation |
| F8 Safety | US-07, US-09, US-10 | X | E5 rubric | Ethics and limitations |
| F9 Teaching | US-06 | X | E5 | Design; Discussion |

---

**Related:** [`01-VISION_AND_SCOPE.md`](01-VISION_AND_SCOPE.md) ·
[`08-UI_UX_SPEC.md`](08-UI_UX_SPEC.md) ·
[`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md) ·
[`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md) ·
[`19-RESEARCH_BRIDGE.md`](19-RESEARCH_BRIDGE.md)
