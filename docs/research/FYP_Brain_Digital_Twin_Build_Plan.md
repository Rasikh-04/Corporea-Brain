# Brain Digital Twin — Build Plan

**Companion to:** [`FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md`](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md)
**Scope of this document:** the engineering plan for a desktop application covering the human body at shell level, with the brain implemented in depth, along the ladder *atlas → disorder mapping → neuronavigation → VR/AR → hardware*.
**Status:** Version 1. Every effort estimate is a hypothesis to be corrected after Rung 1.

---

<a id="reconciliation"></a>

## 0. Reconciling the two documents — this is not a compromise

You said "this is the wrong approach, I know that already." It isn't, and the framing that makes it right is worth internalising because it is also the framing that will get you good marks.

**An FYP is not "research OR software." It is a claim plus the artifact that proves it.** The research plan tells you what claim is defensible. This plan tells you what to construct so the claim can be tested. The failure mode is not "we built something" — the failure mode is *building something that produces no measurable statement about the world*.

So the rule that governs this entire document:

> **Every rung of the ladder must emit at least one number that lands in a results table.**

If a rung cannot produce a number, it is a demo feature, and demo features get built last, cheaply, and are never allowed to consume a month.

That single rule turns your ladder from "scope creep with a nice narrative" into "an incremental system with an evaluation attached at every level." It also means the two documents are not in tension: the [research plan's Part 9](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-9) defines the claims, and the rungs below produce them.

### What changes versus the research plan's recommendation

The research plan recommended narrowing hard. This document keeps the ladder, but makes three moves that let you have both:

1. **Fidelity tiers.** Each rung is built at a declared fidelity level (Demonstrator / Functional / Validated). You climb the whole ladder at Demonstrator fidelity, then deepen only the brain rungs to Validated. Nothing is ever claimed above the tier it was built at.
2. **Stand on 3D Slicer.** See [§2](#stack-decision). This is the single biggest change to the plan and it collapses roughly two years of work into a build configuration.
3. **Phantom, not patient.** The neuronavigation and hardware rungs are executed against a 3D-printed or physical head phantom with known fiducials. That makes them honest, safe, cheap — and, crucially, *measurable*, because a phantom has ground-truth geometry and a patient does not.

---

<a id="rung-map"></a>

## 1. The ladder, restated

Your ladder had five rungs. It is missing three things and one of the five is mis-specified. Here is the corrected version.

| Rung | Name | What it actually is | Emits (the number) | Research-plan link |
|---|---|---|---|---|
| **R0** | **Ingest & spine** | DICOM import, sequence identification, conversion, BIDS layout, patient/study data model, provenance | Ingest success rate across N heterogeneous studies; per-stage wall time | [Hole 9](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-9), [Hole 5](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-5) |
| **R1** | **Atlas & body shell** | Whole-body navigable shell; brain deep-labelled; organ module registry | Label coverage count; render fps at target volume | [Hole 10](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-10), [Tier D](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#tier-d) |
| **R2** | **Patient mapping & disorders** | Segmentation, atlas registration, region attribution, lesion→deficit hypotheses, longitudinal record | **Dice / HD95 / ASSD; region-attribution agreement** — your primary results | [Part 9 E1–E3](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#eval-claims), [Hole 6](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-6) |
| **R3** | **Virtual neuronavigation** | Trajectory planning, probe-eye view, structures-along-path, eloquent proximity warning. **Software only, no tracking.** | Planning task time; proximity-warning agreement vs expert | [Hole 3](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-3), [Tier A](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#tier-a) |
| **R4** | **VR / AR review** | Immersive stereoscopic review of the same scene; controller-based slicing and inspection | Comparative task performance VR vs desktop | [§6.4 Hardware & VR](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hardware-vr) |
| **R5** | **Tracked hardware prototype** | Optically-tracked stylus + head phantom + registration + live pointer display | **Fiducial and target registration error in mm** — a real, publishable number | [§6.4](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hardware-vr) |
| **X** | **Cross-cutting** | QC reporting, evaluation harness, packaging/offline, teaching mode, export, audit log, disclaimer | Offline pass/fail; installer size; reproducibility check | [NFRs](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#nfrs), [Part 10](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-10) |

### What you missed in your original list

- **R0 entirely.** You started at atlas. In practice nothing works until a real study loads. Series descriptions are inconsistent between scanners and vendors, so "which volume is the FLAIR" is a genuine engineering problem, not a formality. Start here.
- **The clinical record.** It is in the research plan as your strongest differentiator ([Hole 6](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-6)) but absent from your build ladder. It belongs in R2.
- **The evaluation harness as a shipped component.** Build the measuring instrument before the features it measures. It is listed in X but should be built during R2.
- **Packaging, offline verification, provenance, QC reports.** Unglamorous, examinable, and cheap if designed in, expensive if retrofitted.

### Fidelity tiers — declare these and never exceed them

| Tier | Meaning | What you may claim |
|---|---|---|
| **D — Demonstrator** | Works on curated data, in a scripted path, under supervision | "We demonstrate that the architecture supports X" |
| **F — Functional** | Works on arbitrary valid input, handles errors, usable by a non-author | "The system performs X on input of type Y" |
| **V — Validated** | Functional, plus measured against ground truth with reported metrics | "The system performs X with measured accuracy Z" |

**Target profile at submission:** R0 = F · R1 = F (brain) / D (body) · R2 = **V** · R3 = F · R4 = D · R5 = D-with-a-number.

Only R2 needs to be Validated. That is where the marks are and where the thesis claim lives. Everything else exists to make R2 usable and the demo compelling.

---

<a id="stack-decision"></a>

## 2. Tech stack — the thing that changes your whole plan

You mentioned Qt + C++ + VTK as your preference, with Rust and Avalonia on hold, and Qt as the middle ground. You also raised using open-source projects as a foundation. **Those two thoughts, combined, point at one answer that is much better than either separately.**

### 3D Slicer *is* a Qt/C++/VTK application

<cite index="84-1">3D Slicer is written mainly in C++ and built on VTK, ITK, CTK, CMake, Qt and Python, with a lean application core plus modules providing specific functionality.</cite> Your intended stack is not merely compatible with Slicer — it is *identical* to Slicer's.

And it is designed to be built upon. <cite index="83-1">The SlicerCustomAppTemplate is a lightweight customisation wrapper around the Slicer core that lets developers add branding, custom code and custom modules</cite>. <cite index="90-1">Customised editions can be generated without modifying Slicer's source, by setting CMake variables for the application name, startup disclaimer, default home module, default favourite modules, and which built-in modules to remove.</cite>

The licensing permits this: <cite index="82-1">the template is Apache-licensed and Slicer itself uses a BSD-style licence, both permissive and supporting unrestricted commercial use with attribution, and any custom code you add may be licensed however you choose.</cite>

### What this buys you, for free, on day one

| You get | Instead of building |
|---|---|
| DICOM import, database, series handling | R0's hardest part |
| Segment Editor with a full manual/semi-auto toolset | Months |
| Registration (rigid, affine, deformable) via ITK/Elastix/ANTs modules | Months |
| GPU volume rendering, MPR, 3D views, transfer functions | Your entire R1/R4 rendering layer |
| Markups, fiducials, rulers, angle tools | R3 primitives |
| Tractography via SlicerDMRI | Years |
| Scene serialisation, undo, extension manager, Python console | Infrastructure you'd never finish |
| Cross-platform build and installer | Weeks of packaging pain |
| A module architecture that *is* your organ-plugin system | Your R1 "whole body modularity" claim, made real |

### The honest cost

- **Build complexity.** The Slicer superbuild compiles its own dependency tree. First successful build on a new machine is realistically a day or two, and it wants disk and RAM. Budget for it and do it *early* — this is your first technical risk to retire, not your last.
- **You inherit a large codebase.** You will spend real time learning Slicer's MRML scene model, module types (CLI / scripted / loadable), and conventions.
- **The "what did you actually build?" question.** An examiner will ask. Your answer must be crisp: *"The platform is Slicer, as declared. Our contribution is the ingest classifier, the region-attribution engine, the deficit-hypothesis layer, the longitudinal record module, the navigation planner, and the evaluation harness — none of which exist in Slicer or any comparable tool."* Write that sentence now and put it in your README.
- **Prototype-vs-product tension.** Python scripted modules are fast to write; C++ loadable modules are faster to run. Prototype in Python, port only what profiling proves needs it.

### Recommended path

**Build a custom Slicer application via SlicerCustomAppTemplate, with your original modules written first as Python scripted modules and selectively ported to C++.**

Do this as a deliberately tested decision, not an assumption:

> **ADR-003 (revised):** Spend one week building three throwaway spikes — (a) a Slicer custom app with one scripted module that loads a case and shows a region label; (b) your existing web POC wrapped in Tauri; (c) a bare Qt/VTK app that loads a NIfTI and renders it. Score each on: time to first useful screen, time to add a second feature, packaging effort, VR path, team learnability. Decide with evidence. **My prediction is (a) wins on everything except VR, and (b) wins VR — see [§7](#hybrid-note).**

This resolves the tension flagged in [Hole 11](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-11): you no longer face "rewrite natively vs stay web," because you are not writing a native application from scratch. You are configuring and extending one that already exists in exactly the stack you wanted.

### Other open-source foundations worth adopting rather than rebuilding

| Need | Use | Notes |
|---|---|---|
| Image-guided intervention modules, pivot calibration, landmark registration | **SlicerIGT** | Purpose-built for exactly R3/R5 |
| Hardware/tracking interface, streaming pose data | **PLUS Toolkit + OpenIGTLink** | <cite index="98-1">Provides an abstraction over vendor APIs and forwards each tracked object's 6-DoF pose as a 4×4 transform over a network connection to Slicer in real time</cite> |
| VR in Slicer | **SlicerVirtualReality** | OpenVR/OpenXR-based; an alternative to the WebXR path |
| Lesion / tumour segmentation | **nnU-Net**, pretrained BraTS models, **MONAI** | Fine-tune, do not invent |
| Brain parcellation | **FastSurfer**, **SynthSeg** | Pretrained, fast, contrast-robust |
| DICOM conversion / server | **dcm2niix**, **Orthanc** | Standard, boring, correct |
| Body-level anatomy | **Z-Anatomy**, **BodyParts3D**, **TotalSegmentator** labels | Check licences; document the known gaps you already found |
| Marker tracking | **OpenCV ArUco / AprilTag** | The cheap optical tracking path for R5 |

**Precedent to cite:** an open-source neuronavigation system for non-invasive brain stimulation has already been published using 3D Slicer with PLUS Toolkit and a camera for tracking. That paper is your architectural reference for R5 *and* your evidence that the approach is credible.

---

<a id="architecture"></a>

## 3. Architecture — how "whole human body" becomes an honest claim

The claim is not "we modelled the human body." The claim is **"we built an organ-agnostic platform and implemented the brain to depth in it."** That is defensible, demonstrable, and true. The architecture is what makes it true rather than rhetorical.

```
┌──────────────────────────────────────────────────────────────┐
│  APPLICATION SHELL  (custom Slicer app: branding, layout,    │
│  home module, disclaimer, curated module set)                │
├──────────────────────────────────────────────────────────────┤
│  BODY LAYER                                                   │
│   • Organ registry (manifest-driven)                          │
│   • Body-level navigation: pick an organ → enter its module   │
│   • Shared: patient record, timeline, provenance, export      │
├──────────────────────────────────────────────────────────────┤
│  ORGAN MODULES  (same interface, different depth)             │
│   ┌───────────────┬──────────────┬──────────────────────────┐│
│   │ BRAIN  (deep) │ EAR (shallow)│ OTHER ORGANS (stub)      ││
│   │ atlas+labels  │ atlas+labels │ atlas mesh + label only  ││
│   │ segmentation  │ disorder map │ "not implemented" state  ││
│   │ attribution   │              │                          ││
│   │ deficits      │              │                          ││
│   │ navigation    │              │                          ││
│   └───────────────┴──────────────┴──────────────────────────┘│
├──────────────────────────────────────────────────────────────┤
│  CORE SERVICES                                                │
│   Ingest · Preprocess · Registration · Segmentation ·         │
│   Atlas/parcellation · Record store · Provenance · Eval       │
├──────────────────────────────────────────────────────────────┤
│  PLATFORM  (Slicer core: MRML scene, VTK render, ITK, DICOM,  │
│  Qt UI, Python, extension manager)                            │
└──────────────────────────────────────────────────────────────┘
```

### The organ module contract

Define this once, in writing, in `ORGAN_MODULE_SPEC.md`. Every organ module declares a manifest:

```yaml
organ: brain
display_name: "Brain"
implementation_level: deep      # deep | shallow | stub
geometry: assets/brain/…
parcellations: [desikan-killiany, harvard-oxford, jhu-wm]
supported_modalities: [MR-T1, MR-T1CE, MR-T2, MR-FLAIR, MR-DWI, CT]
disorders: [ischemic_stroke, glioma, intracerebral_haemorrhage]
capabilities: [segmentation, attribution, deficits, navigation, longitudinal]
provenance: {source: …, licence: …, known_gaps: […]}
```

Three consequences, all of which you want:

1. **The body claim is now structural.** Ship brain (deep), ear (shallow, satisfying your instructor — see [Hole 12](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-12)) and three or four stubs. The UI honestly shows implementation level. Nobody can accuse you of over-claiming because the application itself says "stub."
2. **`known_gaps` is doing real work.** Your Z-Anatomy finding — dural sinuses present but no cerebral veins, cranial nerves clipped at the skull base — becomes a machine-readable, displayed limitation instead of a hidden defect. Turning a known weakness into a declared feature is exactly the move that impresses examiners.
3. **The ear workstream stops being a fork.** It becomes a second instance of one contract, which is *evidence for* the architecture rather than a competitor for time.

### Data model note

The record store, timeline and provenance live at the **body layer**, not inside the brain module. This is the piece that no competitor has ([surviving gaps](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#surviving-gaps)) and it must not be buried in an organ. Specify it in `DATA_MODEL.md` per [Phase 2](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phase-2).

---

## 4. Rung specifications

Effort is given in **engineer-weeks (EW)** at roughly 12–15 focused hours per week. Adjust to your real team size. "Kill criteria" means: if this is true, stop and descope — decided in advance, when you are calm, not in month seven when you are not.

---

<a id="rung-0"></a>

### R0 — Ingest and spine · Target fidelity: **F** · ~3–4 EW

**Build**
- DICOM folder/CD/USB import → study/series tree.
- **Sequence classifier**: identify T1 / T1-CE / T2 / FLAIR / DWI / ADC / SWI / CT from tags plus heuristics. Start with rules over `SeriesDescription`, `ScanningSequence`, `EchoTime`, `RepetitionTime`, `ContrastBolusAgent`; add a small learned classifier only if rules fail. **Always show the guess and let the user correct it** — never silently mis-assign.
- dcm2niix conversion, BIDS-compliant output layout.
- De-identification step with a verification test.
- Patient / Study / Series / Derived-artifact schema with provenance stamping (tool, version, parameters, timestamp).
- QC report per case: orientation check, resolution, missing series, conversion warnings.

**Number it emits:** ingest success rate and sequence-classification accuracy across N heterogeneous studies from ≥3 sources; per-stage wall time.

**Depends on:** [T2 imaging track](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#track-t2) — do the orientation-verification exercise *before* writing this.

**Kill criteria:** none. R0 is mandatory. If R0 is not solid, everything above it is built on sand.

**Watch out for:** the left/right flip. Build the orientation assertion into the pipeline as a hard test with a synthetic asymmetric phantom volume. This is [Risk R5](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-10) and it is the one that silently destroys projects.

---

<a id="rung-1"></a>

### R1 — Atlas and body shell · Target fidelity: **F** (brain) / **D** (body) · ~3–4 EW

**Build**
- Body-level entry screen: navigable whole-body model, organ picker, implementation-level badges.
- Organ registry loading manifests; stub modules render mesh + name + "not implemented in this release."
- Brain module: labelled anatomy from a parcellation atlas, hierarchical tree (system → structure → substructure), click-to-identify both ways (click mesh → highlight in tree, and reverse).
- Layer toggles: cortex / deep grey / ventricles / white-matter tracts / vasculature, each with its `known_gaps` note surfaced in the UI.
- Search by structure name with synonyms.

**Number it emits:** count of uniquely labelled brain structures; render frame rate at target volume size on the reference laptop; body-shell organ count by implementation level.

**Depends on:** [Hole 10](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-10), [Tier D](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#tier-d).

**Kill criteria:** if you find yourself building anatomy *content* (writing textbook descriptions for structures) for more than a few days, stop. Link to external references instead. Content authoring is a bottomless pit and it is the least valuable thing you could be doing — Complete Anatomy has a team on it.

**Deliberately not doing:** physiology animation, muscle/tendon detail, any organ beyond brain and ear at more than stub level.

---

<a id="rung-2"></a>

### R2 — Patient mapping, disorders, and the longitudinal record · Target fidelity: **V** · ~10–14 EW

**This is the FYP.** Everything else is context. Budget accordingly — if you are behind schedule, protect this rung and sacrifice R3–R5.

**Build, in this order**

1. **Preprocessing chain**: reorientation, resampling, bias-field correction, skull stripping, inter-series co-registration, registration to template space. Idempotent, cached, resumable.
2. **Evaluation harness — build this before the segmenter.** Takes predictions + ground truth, emits Dice, HD95, ASSD, volume error, Bland–Altman, and writes the results table automatically. Non-negotiable ordering.
3. **Segmentation**: fine-tuned nnU-Net or pretrained BraTS-lineage model for glioma; stroke lesion model on ATLAS; ICH on CT-ICH. **Report numbers immediately after each.**
4. **Parcellation** via FastSurfer/SynthSeg; handle the tumour mass-effect caveat explicitly (normalisation assumptions break with large mass lesions — document it, don't hide it).
5. **Region attribution**: lesion mask ∩ parcellation → ranked involved regions with percentage overlap and an explicit uncertainty statement.
6. **Tract involvement**: lesion vs white-matter atlas → affected tracts.
7. **Deficit hypotheses**: mapping table from region/tract → expected clinical correlates, each entry carrying a literature citation and a confidence band. **Presented as hypotheses, never conclusions.** Honour the clinician's guidance that missing is worse than over-flagging by ranking rather than filtering — show everything, ordered, never suppress ([Hole 3](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-3)).
8. **Longitudinal record**: structured history (age, sex, **handedness**, comorbidities, medications, allergies, addiction, occupation, marital status, obstetric history), family history + genogram, standardised scores. **Use a licence-clean cognitive instrument — not MMSE ([Hole 8](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-8)).**
9. **Timeline view**: scans, scores, events, medications on one axis; lesion volume trend; prior-vs-current comparison view.
10. **Structured report export** with provenance.

**Numbers it emits:** [E1, E2, E3](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#eval-claims) — Dice/HD95/ASSD per disorder; region-attribution agreement vs expert reading; longitudinal change-detection reliability. These are your Chapter 4 tables.

**Kill criteria:** if two disorders are not at Validated fidelity by the end of Phase 3, cut R3–R5 entirely and deepen R2. A thesis with one deeply validated capability beats one with five shallow ones, every time.

---

<a id="rung-3"></a>

### R3 — Virtual neuronavigation · Target fidelity: **F** · ~4–5 EW

**Be precise about what this word means.** Clinical neuronavigation means a tracked instrument registered to a physical patient in an operating theatre. You are not building that, and [Tier A](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#tier-a) already owns it. What you are building is **pre-operative trajectory planning and virtual approach review** — software-only, on imaging, with no patient contact and no regulatory claim.

**Build**
- Entry point + target point placement on the patient volume (Slicer markups give you this).
- Trajectory line with length, angle, and a **probe-eye view** (camera looking down the trajectory axis).
- **Structures-along-path**: ray-cast the trajectory through the parcellation and report every structure traversed, in order, with entry/exit depths.
- **Eloquent proximity warning**: minimum distance from trajectory to each eloquent region and each critical tract, with a configurable threshold and a ranked warning list.
- Multi-trajectory comparison: place 2–3 candidate approaches, compare on traversed structures and minimum eloquent distance.
- Approach report export.

**Number it emits:** planning task completion time; agreement between the system's proximity warnings and an expert's assessment on N cases; count of trajectories where the system identified a traversed structure the reviewer had not noted.

**Why this is genuinely worth building:** it is the direct expression of your neurologist's volunteered concern about eloquent areas and safer surgery, it runs entirely on data you already have, and the "structures traversed, in order, with depths" output is a concrete artifact no free tool hands you.

**Kill criteria:** if R2 is not at Validated by the Phase 3 gate, defer this whole rung.

**Explicitly not doing:** brain shift compensation, intra-operative anything, instrument tracking against a patient, registration to a real head.

---

<a id="rung-4"></a>

### R4 — VR / AR review · Target fidelity: **D** · ~2–4 EW

**Two viable paths. Pick based on the [§2](#stack-decision) spike outcome.**

| Path | How | Cost | Trade-off |
|---|---|---|---|
| **SlicerVirtualReality** | Extension on your custom Slicer app; OpenVR/OpenXR | Low if Slicer path chosen | Stays in one codebase; tethered PC VR |
| **WebXR** | Export scene to your existing web/R3F POC; run on Quest standalone | Low if web POC maintained | Standalone headset, easy demo, but a second codebase |

<a id="hybrid-note"></a>
**The hybrid worth considering:** keep the web POC alive purely as a *viewer/VR front-end* fed by files the Slicer app exports. You get the desktop app in the stack you want *and* the cheap standalone VR demo, without maintaining two full applications — the web side becomes a thin renderer with no analysis logic. Costs maybe 1 EW of export plumbing. This directly resolves the tension noted in [Hole 11](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-11).

**Build:** load a real case scene in VR; grab/rotate/scale; controller-driven clipping plane; point at a structure to identify it; view a planned trajectory from R3 in stereo.

**Number it emits:** comparative task performance — e.g. time and accuracy for "identify which lobe this lesion primarily involves" or "judge whether trajectory A or B passes closer to the corticospinal tract," VR versus desktop, with 6–10 participants (students are acceptable subjects for a spatial-judgement task; state that limitation).

**AR note:** phone/tablet AR that overlays the model on a physical phantom is achievable with marker tracking, and is a nice demo. Overlaying on a real person with clinical accuracy is not. Do the former, claim only the former.

**Kill criteria:** if it is not working within 2 EW, ship a recorded video and move on. VR is a showpiece, not a claim.

---

<a id="rung-5"></a>

### R5 — Tracked hardware prototype · Target fidelity: **D, with a real number** · ~4–6 EW

This is where your instructor's "no hardware" concern gets addressed properly: **you are not building a medical device, you are building a measurement demonstrator against a phantom.** That reframing makes it small, safe, honest, and — the key property — *quantifiable*.

**The setup**

```
   Webcam (or stereo pair)
          │  sees
          ▼
   ┌─────────────────┐        ┌──────────────────┐
   │ Reference marker│        │ Stylus w/ marker │
   │ fixed to phantom│        │ + known tip      │
   └────────┬────────┘        └────────┬─────────┘
            │                          │
            └──── PLUS Toolkit ────────┘
                  (pose → 4×4 transforms)
                        │ OpenIGTLink
                        ▼
             Your Slicer-based application
             • pivot calibration (stylus tip)
             • landmark registration (phantom ↔ image)
             • live pointer position in image space
             • distance-to-target readout
```

**Hardware ladder — climb only as far as you need**

| Tier | Tracking | Cost | Accuracy | Verdict |
|---|---|---|---|---|
| **H0** | Mouse/keyboard | 0 | n/a | Baseline for comparison |
| **H1** | VR controller as stylus (Quest Touch) | Headset only | Sub-cm, good | **Cheapest real 6-DoF.** Merges R4 and R5 |
| **H2** | Webcam + printed ArUco markers on a 3D-printed stylus | ~$20–60 | Few mm, lighting-dependent | **Recommended.** Mirrors how real optical navigation works |
| **H3** | Stereo/depth camera, or passive arm with rotary encoders | ~$150–400 | Better, more work | Only if H2 accuracy is embarrassing |
| **H4** | Commercial optical tracker (NDI Polaris etc.) | Thousands | Sub-mm | Out of budget. Cite as the clinical standard |

**Recommended: H2, with H1 as fallback.** H2 uses a standard webcam and printed markers; PLUS supports webcam-based ArUco tracking and streams poses to Slicer, and SlicerIGT provides the pivot-calibration and landmark-registration modules you need. There is an existing SlicerIGT training project that ships printable ArUco markers, PLUS configs, and STLs for a calibration stylus and pivot block — **read that repository before designing anything.**

**The phantom:** 3D-print or otherwise obtain a head model with ≥6 well-distributed fiducial divots at *known* coordinates. Then CT or MRI it if you have access, or generate the model from a public head scan so you have image-space ground truth by construction. This is what makes the whole rung measurable.

**Numbers it emits — the good ones**
- **Pivot calibration RMS error** (mm) for the stylus tip.
- **FRE** — fiducial registration error after landmark registration.
- **TRE** — target registration error at points *not* used in registration. This is the meaningful one and it is the standard metric in the field.
- Tracking latency and jitter; working volume; failure rate under marker occlusion and varying lighting.

A results table reporting TRE in mm for a $40 optical tracking setup, honestly compared against published sub-millimetre figures for commercial systems, is a genuinely good FYP result. It is real engineering with a real measurement, and it makes no clinical claim whatsoever.

**On haptics — be straight about it.** A vibration motor giving a proximity cue is *vibrotactile feedback*, which is legitimate and cheap. **Force feedback** — resisting your hand as tissue would — requires an actuated device and a tissue model, and is the core intellectual property of the commercial simulators. Do not describe a vibrating stylus as haptic surgical simulation; describe it as a proximity cue, measure whether it improves targeting accuracy versus visual-only, and you have another honest number.

**Kill criteria:** if PLUS + camera calibration is not producing stable poses within 2 EW, drop to H1 (VR controllers) which needs no calibration at all. If that also fails, ship R5 as a design + simulation with the tracking stubbed, and say so.

**Safety framing for the report:** phantom only, no human subjects, no clinical use, no accuracy claim transferable to patients.

---

<a id="cross-cutting"></a>

### X — Cross-cutting work · ~3–4 EW spread throughout

- **Evaluation harness** (build during R2, first).
- **QC report generator** per case.
- **Provenance/versioning** threaded through every derived artifact.
- **Packaging + offline verification**: installer, and a test that runs the full pipeline with networking disabled. This is a headline claim for your target setting ([Hole 9](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-9)) so *test it deliberately*.
- **Teaching mode**: anonymised case library, guided walkthrough. Cheap on top of everything else, and serves the low-risk second user group.
- **Disclaimer + audit log + encryption at rest.**

---

<a id="timeline"></a>

## 5. The merged timeline

Research and build interleaved. Research phase numbers refer to [Part 7 of the research plan](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phases). Weeks are relative to your start.

| Weeks | Research track | Build track | Gate |
|---|---|---|---|
| **1–2** | [Phase 0](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phase-0) — decide scope, memo to instructor, ethics enquiry sent | **Stack spikes** (a/b/c). Get one Slicer superbuild compiling on one machine | Scope statement written; ADR-003 decided with evidence |
| **3–7** | [Phase 1](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phase-1) — landscape review, datasets acquired, neurologist round 2, legal audit | **R0** ingest + spine. Everyone works through Slicer tutorials in parallel | Real DICOM study loads, converts, orientation-verified |
| **8–12** | [Phase 2](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phase-2) — SRS, data model, imaging pipeline spec, wireframes | **R1** atlas + body shell; **evaluation harness** | Clinician has criticised the wireframes; harness computes Dice on a dummy pair |
| **13–22** | [Phase 3](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phase-3) — vertical slice, measured | **R2** — the whole rung. Stroke first, then glioma | **Hard gate: real numbers in a table for ≥1 disorder.** If not met, cut R3–R5 now |
| **23–28** | [Phase 4](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phase-4) — second disorder, longitudinal, clinician sessions | **R3** navigation planner; R2 hardening | Two disorders at Validated; E5 sessions scheduled |
| **27–31** | Clinician evaluation, external validation if data landed | **R4** VR + **R5** hardware, in parallel by different owners | TRE number obtained, or R5 descoped per kill criteria |
| **30–33** | Results analysis | **X** — packaging, offline test, teaching mode, polish | Offline test passes; installer produced |
| **33–38** | [Phase 5](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phase-5) — thesis, demo video, viva prep | Freeze. Bug fixes only | Demo rehearsed end to end ≥3 times |

**Three scheduling rules:**

1. **Weeks 13–22 are sacred.** R2 is the thesis. Nothing gets to interrupt it — not the ear app, not a VR idea, not a stack re-litigation.
2. **R4 and R5 run in parallel, owned by different people.** They are independent and both are optional. This is where a larger team pays off.
3. **Write from week 3.** The landscape review, competitor teardown, legal memo and evaluation protocol are already thesis chapters ([Risk R11](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-10)).

---

<a id="demo"></a>

## 6. Design backward from the demo

Write this script now and build toward it. A 12-minute demonstration, one rung per beat.

| Min | Beat | Rung | The line you say |
|---|---|---|---|
| 0–1 | Body shell. Rotate, pick brain. Badges show brain=deep, ear=shallow, rest=stub | R1 | "The platform is organ-agnostic. The brain is our reference implementation." |
| 1–2 | Brain atlas. Click a gyrus, tree highlights. Toggle tracts. A `known_gaps` note appears on the vascular layer | R1 | "Limitations are declared in the model, not hidden." |
| 2–4 | Load a real DICOM study from a USB stick. Sequences auto-identified, one correction made by hand. QC report shown | R0 | "No PACS, no server, no internet." |
| 4–7 | Segmentation runs. Lesion appears. Region attribution table with percentage overlap. Tract involvement. Deficit hypotheses with citations and confidence | R2 | "This is where our contribution is, and here are the numbers." **Show the results table.** |
| 7–8 | Timeline: prior scan, current scan, volume trend, score trend, genogram | R2 | "Nothing else puts imaging quantification and the clinical record on one axis." |
| 8–9 | Place entry and target. Probe-eye view. Structures traversed, in order, with depths. Eloquent proximity warnings ranked | R3 | "Planning support. Not navigation, not intra-operative, no clinical claim." |
| 9–10 | Headset on, same case in VR, controller slices through it | R4 | "The same scene, immersively." |
| 10–12 | Phantom on the desk. Stylus touches a divot. Cursor moves in image space. **TRE number on screen** | R5 | "Forty dollars of hardware. Here is our target registration error, and here is the commercial benchmark." |

If you can perform that, you have an FYP that is both research-grounded and visibly real. Note that the *centre of gravity* is minutes 4–8 — that is deliberate, and your rehearsal should protect it if you run over.

---

<a id="chapter-map"></a>

## 7. Rung → chapter → claim mapping

So that nothing you build is orphaned from the thesis.

| Rung | Thesis chapter | Evaluation claim | Section of research plan |
|---|---|---|---|
| R0 | Methods: data & pipeline | Ingest robustness, timings | [Hole 5](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-5), [Hole 9](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-9) |
| R1 | Design & implementation; Related work | Coverage, render performance | [Tier D](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#tier-d), [Hole 10](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-10) |
| R2 | **Results — the core chapter** | **E1, E2, E3** | [Part 9](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#eval-claims) |
| R3 | Design; Results (secondary) | Planning task time, expert agreement | [Hole 3](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-3) |
| R4 | Design; Results (secondary) | VR vs desktop task performance | [§6.4](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hardware-vr) |
| R5 | Results (secondary); Future work | FRE/TRE, latency, robustness | [§6.4](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hardware-vr) |
| X | Implementation; Limitations | E4 offline/resource compliance | [NFRs](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#nfrs) |
| — | Ethics & limitations | — | [Hole 8](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-8), [track T7](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#track-t7) |

---

<a id="build-risks"></a>

## 8. Build-specific risks

These are additional to the [research risk register](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-10).

| # | Risk | L | I | Mitigation |
|---|---|---|---|---|
| B1 | Slicer superbuild fails or takes weeks | Med | High | Retire in week 1–2 as a spike. Have the Tauri/web fallback pre-scored |
| B2 | Team stalls learning Slicer's MRML/module model | Med | High | Everyone does the Slicer tutorials in weeks 3–7 in parallel with R0. Prototype in Python |
| B3 | "What did you actually build?" at viva | High | High | Write the contribution sentence in the README now; keep a `CONTRIBUTIONS.md` listing every original module |
| B4 | Ladder climbing beats depth — five shallow rungs, no numbers | High | Critical | The one-number-per-rung rule; the week-22 hard gate |
| B5 | Sequence classifier mis-assigns silently | Med | High | Always display the guess; always allow correction; log every assignment |
| B6 | Camera tracking too jittery for a credible R5 | Med | Med | H1 (VR controllers) fallback; kill criteria at 2 EW |
| B7 | Ear module quietly grows into a second product | High | High | Ear is **shallow tier** in the manifest. Enforce via the organ contract |
| B8 | Atlas content authoring becomes a time sink | Med | Med | Link out to external references; never write anatomy prose |
| B9 | Licensing violation shipped (instrument, asset, dataset) | Med | High | Licence audit in Phase 1; `.gitignore` discipline; manifest carries `licence` field |
| B10 | Two codebases (Slicer + web) both half-maintained | Med | Med | If hybrid, web side is a *thin viewer only*, zero analysis logic. Written into ADR |

---

<a id="fallback"></a>

## 9. The fallback — what "minimum acceptable" looks like

Decide this now, so that if month six goes badly you descope calmly instead of panicking.

**Minimum viable FYP** (still a good project):
- R0 at F, R1 at F for brain only, **R2 at V for one disorder**, X packaging.
- Body shell present with stubs; ear shallow.
- No R3, R4, R5. Each documented as designed-not-built, with the design included.
- One results chapter with real Dice/HD95 numbers and a region-attribution agreement table.

That is a complete, honest, defensible FYP. Everything above it is upside.

**What is never acceptable:** all five rungs at Demonstrator fidelity with no numbers anywhere. That is a tech demo, and it will be marked as one.

---

<a id="repo"></a>

## 10. Repository layout

Both documents live together, which is what makes the cross-links work.

```
fyp-brain-digital-twin/
├── README.md                      ← contribution sentence lives here
├── docs/
│   ├── FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md
│   ├── FYP_Brain_Digital_Twin_Build_Plan.md      ← this file
│   ├── VISION_AND_SCOPE.md
│   ├── NON_GOALS.md
│   ├── SRS.md
│   ├── DATA_MODEL.md
│   ├── IMAGING_PIPELINE.md
│   ├── ORGAN_MODULE_SPEC.md
│   ├── EVALUATION_PROTOCOL.md
│   ├── LEGAL_AND_ETHICS.md
│   ├── CONTRIBUTIONS.md
│   ├── COMPETITOR_TEARDOWN.md
│   ├── DECISIONS/                 ← ADR-001, ADR-002, …
│   └── LITERATURE/                ← research brief outputs + your commentary
├── app/                           ← custom Slicer application
│   ├── Modules/
│   │   ├── Ingest/
│   │   ├── OrganRegistry/
│   │   ├── BrainAtlas/
│   │   ├── LesionAnalysis/
│   │   ├── RegionAttribution/
│   │   ├── ClinicalRecord/
│   │   └── TrajectoryPlanner/
│   └── Resources/                 ← branding, stylesheets
├── organs/                        ← manifests + assets (assets gitignored if licensed)
├── pipeline/                      ← preprocessing, segmentation, batch jobs
├── eval/                          ← harness, metrics, results tables
├── hardware/                      ← STLs, PLUS configs, marker PDFs, calibration
├── scripts/                       ← dataset downloaders (never the data itself)
├── CLAUDE.md
└── HANDOFF.md
```

Both markdown files use explicit `<a id="…">` anchors, so links survive heading edits. When you rename a file, update the links in the other one — put that in a pre-commit checklist.

---

<a id="next"></a>

## 11. First fourteen days, build track

Runs alongside the research-track fortnight in [Part 12](./FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-12).

| Day | Action | Owner |
|---|---|---|
| 1–2 | Read [§2](#stack-decision) with the team. Agree the three spikes and who owns each | Lead |
| 2 | Start the Slicer superbuild on the strongest machine. **Start it early; it is slow** | Build owner |
| 3–5 | Spike A: custom Slicer app via SlicerCustomAppTemplate + one scripted module that loads a NIfTI and prints a region label | Owner A |
| 3–5 | Spike B: existing web POC wrapped in Tauri, offline, loading a local file | Owner B |
| 3–5 | Spike C: bare Qt + VTK app rendering a NIfTI volume | Owner C |
| 5 | Order/print: webcam, ArUco marker sheet, head phantom STL queued for printing. **Long lead item — order in week 1** | Hardware owner |
| 6 | Draft `ORGAN_MODULE_SPEC.md` — the manifest schema | Architect |
| 7 | Spike review. Score on the six criteria. Write **ADR-003** | All |
| 8–11 | Work through 3D Slicer user tutorials — everyone, not one person. Then SlicerIGT tutorials U-11 (pivot calibration) and U-12 (landmark registration) | All |
| 8–11 | Begin R0: DICOM import + sequence classifier rules, on ≥3 studies from different sources | Build owner |
| 12–13 | Orientation verification test with a synthetic asymmetric volume. Make it a CI test | Build owner |
| 13 | Write `CONTRIBUTIONS.md` v1 and the README contribution sentence | Lead |
| 14 | Joint gate with the research track: scope confirmed, ADR-003 written, a real study loads | All |

---

## 12. Sources for this document

- 3D Slicer developer FAQ — architecture and dependency stack (C++, VTK, ITK, CTK, CMake, Qt, Python). https://www.slicer.org/wiki/Documentation/Nightly/Developers/FAQ
- Kitware — *SlicerCAT: Creating custom applications based on 3D Slicer*, including licensing. https://www.kitware.com/slicercat-creating-custom-applications-based-on-3d-slicer/
- Kitware — *SlicerCAT and Python: Creating Custom Slicer Applications with Qt Stylesheets*. https://www.kitware.com/slicercat-and-python-creating-custom-slicer-applications-with-qt-stylesheets/
- SlicerCustomAppTemplate repository. https://github.com/KitwareMedical/SlicerCustomAppTemplate
- Slicer build configuration — custom application CMake variables. https://www.slicer.org/w/index.php/Documentation/Nightly/Developers/Build_Instructions/Configure
- SlicerIGT user tutorials — pivot calibration, landmark registration, optical tracking. https://www.slicerigt.org/wp/user-tutorial/
- SlicerIGT OMTCentralLineTraining — printable ArUco markers, PLUS configs, calibration stylus and pivot block STLs. https://github.com/SlicerIGT/OMTCentralLineTraining
- PLUS Toolkit / OpenIGTLink. https://openigtlink.org/users/
- *Open-source neuronavigation for multimodal non-invasive brain stimulation using 3D Slicer* — architectural precedent for R5. https://arxiv.org/pdf/1909.12458
- SlicerDMRI. https://dmri.slicer.org/

---

*End of build plan. Version 1. Revise after the week-7 spike review — that is the first point at which you will know something you don't know now.*
