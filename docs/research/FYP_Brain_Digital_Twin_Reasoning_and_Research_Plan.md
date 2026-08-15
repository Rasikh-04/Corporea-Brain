# Brain Digital Twin — Project Reasoning, Landscape Audit, and Research Plan

**Prepared for:** Rasikh + FYP team, UET Lahore
**Status:** Working document. Version 1. Everything here is arguable — argue with it.
**Purpose:** Convert a broad, half-defined ambition into a defensible FYP with a scope, a thesis, an evidence base, an evaluation plan, and a study schedule.

**Companion document:** [`BUILD_PLAN.md`](./FYP_Brain_Digital_Twin_Build_Plan.md) — the parallel engineering plan for the desktop application. This document decides *what is true and what is worth doing*; the build plan decides *what gets constructed and in what order*. They are two views of one project. Every build rung in the companion document is designed to emit a measurable result that lands in [Part 9](#part-9) of this one.

---

## How to read this document

There are twelve parts. They are ordered so that each one constrains the next.

| Part | What it does | Read when |
|---|---|---|
| 0 | The blunt verdict | Now |
| 1 | What you actually have today | Now |
| 2 | The holes in the current concept — the audit | Now, with the team |
| 3 | What already exists, and what it kills | Before you talk to the instructor again |
| 4 | Candidate theses, scored, with a recommendation | Team decision meeting |
| 5 | Requirements skeleton (scope / non-goals / SRS spine) | After Part 4 is settled |
| 6 | Feasibility: data, compute, skills, time, hardware | Alongside Part 5 |
| 7 | The learning + research plan (tracks, schedule, ownership) | The main operational answer |
| 8 | How to use each tool (Science / Code / chat / literature) | While executing Part 7 |
| 9 | Evaluation plan — how you prove anything at all | Non-negotiable, design it early |
| 10 | Risk register | Weekly review |
| 11 | Questions to force decisions (instructor / neurologist / team) | Immediately |
| 12 | The next 14 days | Immediately |

The single most important sections are **Part 2 (holes)**, **Part 4 (thesis)**, and **Part 9 (evaluation)**. Everything else is scaffolding.

---

<a id="part-0"></a>

# Part 0 — The blunt verdict

**Your concept document describes four different products stacked on top of each other, and only one of them is an FYP.**

The four are:

1. An interactive anatomical atlas of the human body.
2. A disorder knowledge base (textbook content, structured).
3. A patient-specific imaging visualisation and record system.
4. A predictive/simulative digital twin capable of proactive treatment and surgical rehearsal.

Product 1 is a solved commodity — you cannot compete and you gain nothing by trying. Product 2 is a content problem, not an engineering problem, and it is also solved. Product 4 is a decade-long, RCT-scale research programme that a European consortium with a €-funded infrastructure is still working through. **Product 3 is the only one with a real, unclaimed gap in it, and it is the only one you can build, evaluate, and defend in the time you have.**

Three further hard truths, drawn from your own interview notes:

- **Your neurologist told you clinical diagnosis is ~99% accurate and imaging carries ~30% of the diagnostic weight.** That single line invalidates "AI-assisted diagnosis" as a value proposition. If the clinician is already near-ceiling, a diagnostic aid has almost no headroom and enormous risk. The value is *not* in telling the doctor what the disease is. It is in **localisation, quantification, longitudinal comparison, communication, and record continuity** — things humans do slowly, inconsistently, or not at all.
- **"We modeled everything static"** — you flagged this yourself in the document. A static 3D model with lesions painted on it is a *visualisation twin*, not a digital twin. That is fine, but you must say so explicitly or a competent examiner will destroy the claim.
- **Datasets are correctly identified as your bottleneck, but you have mis-ranked the real bottleneck.** The real bottleneck is *ground truth and evaluation*. You can get imaging data. You cannot easily get the paired clinical annotations that let you say "our output was correct." Design the evaluation first; let it dictate the data you chase.

**Recommendation in one sentence:** Reframe the FYP from *"a digital twin of the brain"* to *"an open, offline-capable, patient-centred neuro imaging + record workstation that produces quantified, longitudinally comparable, anatomically localised views of a patient's brain for stroke and glioma, designed for low-resource clinical settings"* — and position the full digital twin as the research vision the architecture is built toward, not the deliverable.

That reframe keeps every word of your ambition alive in the introduction chapter while giving you something you can actually finish, measure, and defend.

---

<a id="part-1"></a>

# Part 1 — Where you actually are today

Reconstructed from your project history so the rest of this document is grounded in reality, not aspiration.

### Assets you have

| Asset | State | Value to the FYP |
|---|---|---|
| **Brain POC** — Next.js + React Three Fiber + Niivue + Supabase, 3D brain with disorder mapping | Working, demoed, instructor-approved in principle | High. Proves rendering + data pipeline feasibility. This is your credibility anchor. |
| **Multi-disorder case data** — ATLAS (ischemic stroke), PhysioNet CT-ICH (haemorrhage), BraTS (tumour), OASIS (Alzheimer's), CHB-MIT/TUH (epilepsy EEG); 3–6 cases per disorder after instructor feedback on positional/intensity variety | Downloaded, partially processed | High for demo, **low for evaluation** — a handful of cases proves rendering, not performance. |
| **Anatomy assets** — Z-Anatomy derived (FBX), with known gaps: dural sinuses only, no cerebral veins; cranial nerves clipped at skull base | Documented in ASSET_SOURCING.md | Medium. Good enough for teaching/visual context, **not** good enough for anything vascular or surgical. This limitation must be written down in the scope. |
| **Ear POC** — instructor-assigned, web-based, rebuild from scratch (seniors' code correctly judged unusable) | In progress / assigned | **Scope risk.** See Part 2, Hole 12. |
| **Clinical contact** — neurologist interview completed, structured questionnaire (Sections A–K) partially answered | Round 1 done; several sections (notably B4, E5) unanswered | Very high. Access to a clinician is the scarcest resource in this project. Protect it, use it deliberately. |
| **Desktop port research** — Qt/C++/VTK vs Rust/wgpu vs Avalonia/.NET benchmarking protocol drafted | Planned, not executed | **Probably premature.** See Part 2, Hole 11. |
| **AI-augmented workflow** — Claude Code driven, structured planning pipelines, Fedora dev environment | Mature | High. This is a genuine force multiplier for a small team on a break. |

### Constraints you are operating under

- **Software-only mandate** from the instructor (hardware judged out of time-budget).
- **Team dispersed** over summer break; coordination is failing.
- **Instructor direction is inconsistent** — brain POC approved, then ear rebuild assigned, with the relationship between them unclear.
- **No confirmed access to real patient data** — 300–500 cases mentioned in notes as an aspiration, not a commitment.
- **No ethics/IRB process started.**
- Third-year students; final-year FYP timeline; realistically **8–10 months of part-time capacity across a small team.**

### The three things that are currently ambiguous and are costing you the most

1. **Is the deliverable the brain system, the ear system, or a unified platform?** Nobody has decided. Everything downstream is blocked on this.
2. **Is the FYP a visualisation tool, a decision-support tool, or a simulation research artifact?** These have completely different evaluation standards and completely different chapter structures.
3. **Are you getting real patient data, or are you building and evaluating entirely on public datasets?** This is a 6-month lead-time question and it is not being worked on.

Resolve these three in the next two weeks or the project will drift until March.

---

<a id="part-2"></a>

# Part 2 — The holes: an audit of the current concept

Each hole is stated, then what it actually means, then what to do about it. These are ordered roughly by how much damage they do.

---

<a id="hole-1"></a>

### Hole 1 — "Digital twin" is undefined, and the field itself is currently fighting about the definition

Your document uses "digital twin" to mean everything from "a nice 3D model" to "a system you can perform proactive treatment on." These are not the same thing, and the literature has recently become quite hostile to the loose usage.

The current consensus in neurology is roughly: a strict digital twin should be **individualised, dynamically updated, mechanistically or physiologically informed, and bidirectionally connected to decision-making.** A 2026 review in the *Journal of Integrative Neuroscience* argues that most published "digital twins" in neurology are more honestly described as *twin-inspired longitudinal decision-support or trial-analytics models*, and that the field's progress is limited by gaps in measurement validity, uncertainty handling, and prospective evaluation. A 2026 Frontiers perspective makes the same complaint: the term risks being applied to any predictive model that does not actually simulate biological dynamics.

**A useful three-tier framing to adopt in your report:**

| Tier | Name | What it does | Examples | Where you'd land |
|---|---|---|---|---|
| **T1** | **Visualisation twin** | Patient-specific 3D representation from real scans; lesions localised, structures labelled. No prediction. | 3D Slicer reconstructions; Brainlab Elements rendering; your current POC | **Where you are** |
| **T2** | **Quantitative / statistical twin** | Adds derived measurements, longitudinal tracking, atlas-based region attribution, population comparison, risk stratification. Predicts *statistically*, not mechanistically. | Most "digital twin" papers in stroke and Alzheimer's | **Where you can realistically get** |
| **T3** | **Mechanistic twin** | Simulates brain dynamics with personalised parameters; supports virtual intervention. | The Virtual Brain / Virtual Epileptic Patient; Digital Twin Brain (Fudan) | **Where the vision is** — out of FYP reach |

**Action:** Put this table in Chapter 1 of your report. Declare that you are building T1→T2 with an architecture designed for T3. This single move converts your biggest vulnerability (over-claiming) into a strength (conceptual clarity).

---

<a id="hole-2"></a>

### Hole 2 — There is no stated user, no stated moment of use, and therefore no requirements

Your document describes capabilities. It never says: *who opens this application, on what device, at what point in the patient's journey, with how many minutes available, and what decision changes as a result.*

Without that, every requirement is unfalsifiable and every feature is arguable forever. Your interview notes actually contain the answer and you have not extracted it:

- Diagnostic flow is **History → Examination → Investigation → Medication**.
- Panel always includes a **radiologist**; neurosurgeon joins when surgery is indicated.
- Imaging is **mandatory before surgery**.
- Clinic scheduling exists (**Tue & Thu, 10–12**) — i.e. there is a finite, crowded consultation window.
- The **eloquent areas** concept was volunteered specifically in the context of safer surgery.

That maps to at least four distinct users with four distinct moments:

| User | Moment | Time available | What they need |
|---|---|---|---|
| Neurologist | Outpatient consult, reviewing a new/returning patient | 5–10 min | Fast summary; has anything changed since last visit; structured history |
| Neuroradiologist | Reporting a study | 10–30 min | Quantification, comparison to prior, not another viewer |
| Neurosurgeon | Pre-op planning | 30–90 min | Lesion relative to eloquent areas and tracts; approach |
| Trainee / student | Learning | Unbounded | Explanation, anatomy, correlation with clinical picture |

**Action:** Pick **one primary user** and **one secondary**. Write 5–8 user stories in the form *"As a [user], at [moment], I need [capability], so that [decision] changes."* If a feature does not serve a story, it is out of scope. My recommendation for primary user is in Part 4.

---

<a id="hole-3"></a>

### Hole 3 — The value proposition collides head-on with your own interview data

Your notes: **clinical diagnostic accuracy ~99%; imaging contributes ~30% of diagnostic weight.**

If you build a system whose pitch is "assists the doctor with diagnosis and provides insight and another perspective," you are pitching into a 1% gap, in a domain where errors are catastrophic, against a clinician who has already told you he does not need it.

But the same interview hands you what he *does* need, and you have not noticed:

- He needs **imaging** — mandatory before surgery, ranked necessity: ischemic stroke, haemorrhagic stroke, glioma > dementia (age-dependent) > epilepsy (may or may not).
- He needs **eloquent area awareness** for safe surgery.
- He needs **structured history** — age, sex, handedness, comorbidities, family history, addiction, occupation, marital status, allergies, obstetric history. That is a *lot* of structured fields, and handedness in particular he called out as critical.
- He explicitly said **missing something is far worse than over-flagging it.** That is a design constraint on every alert you build, and it defines your operating point on the sensitivity/specificity curve.
- He said **MMSE-type cognitive questionnaires can and should live in the app**, while physical scores like GCS need in-person evaluation.

**Action:** Rewrite the value proposition. Something in the shape of: *"We do not diagnose. We make the 30% imaging contribution quantitative, spatially explicit, and longitudinally comparable, and we make the structured clinical record that surrounds it complete and reusable."* That is defensible, matches the interview, and nobody in the room can call it over-claiming.

---

<a id="hole-4"></a>

### Hole 4 — No ground truth, therefore no possible claim of correctness

This is the hole that most FYPs of this type die in. You have segmentation masks from public datasets — good. But the moment you say "this system localises the lesion to these regions and these are the expected deficits," you need a reference standard that says whether that was right.

You currently have:
- Public datasets with **lesion masks** (ATLAS, BraTS, CT-ICH) → lets you evaluate *segmentation overlap*. Fine.
- Nothing that lets you evaluate *region attribution*, *clinical relevance*, or *usefulness*.

**Action:** Design the evaluation before you build (Part 9). Minimum viable evaluation for an FYP of this kind:
1. **Segmentation/overlay accuracy** vs public ground truth — Dice, HD95, ASSD. Purely computational, no clinician needed.
2. **Region-attribution agreement** — take N cases with existing radiology reports, have your system output affected regions, compare to the report's stated location. Needs a clinician for ~20–30 cases.
3. **Structured expert review** — your neurologist reviews M retrospective cases in your tool and scores usefulness on a defined rubric.
4. **Usability** — SUS questionnaire, task completion time, with 5–8 clinicians or trainees.

Items 1 and 4 you can do without patient data. Items 2 and 3 require the clinical relationship. Start 2 and 3 as procurement tasks *now*.

---

<a id="hole-5"></a>

### Hole 5 — The data plan is a list of dataset names, not a data architecture

You correctly identify four layers (structural / functional / disease-specific / patient-specific). What is missing is: *what does one patient record look like in your system, in a schema, with types and units and provenance.*

Concretely, the missing pieces:
- **Coordinate space discipline.** You are mixing datasets in different orientations and resolutions. You need a declared canonical space (e.g. MNI152 for group/atlas work, native subject space for per-patient display), a documented registration path, and an explicit statement of where atlas labels come from and their limitations. This is the single most common source of silent, invisible errors in projects like yours — the lesion lands in the wrong lobe and everything downstream is confidently wrong.
- **Atlas/parcellation choice.** Desikan-Killiany, Destrieux, AAL3, Harvard-Oxford, Schaefer, JHU white-matter atlas — each has different granularity, different licensing, and different clinical interpretability. Pick, justify, document, and be consistent.
- **Provenance and versioning.** Every derived artifact (mask, mesh, measurement) must record: source series, tool + version, parameters, date. Without this, nothing is reproducible and Chapter 4 becomes unwritable.
- **De-identification pipeline.** DICOM headers contain a lot of PHI. If you ever touch a real hospital scan, you need a defined, tested de-identification step *before* the data leaves the hospital machine. Face-defacing for T1 MRI is a specific, non-obvious requirement.
- **Data model for the clinical layer.** All those history fields from the interview need a schema, with controlled vocabularies where possible (ICD-10 for diagnoses, SNOMED CT concepts if you can, LOINC for observations). Rolling your own free-text fields will be flagged in review.

**Action:** Produce a `DATA_MODEL.md` and a `IMAGING_PIPELINE.md` as first-class deliverables in Phase 2. These are examinable artifacts on their own.

---

<a id="hole-6"></a>

### Hole 6 — "Record-keeping down the generations" is your best original idea and it is buried in one sentence

Read this line from your own document again:

> "the record-keeping is a best tool to send it down the generation."

Combined with the neurologist's emphasis on **family history, anamnesis, and genogram**, and on **comorbidities**, this is the most differentiated idea in the entire document, and it appears once, as an afterthought.

Nobody's neuronavigation system does longitudinal, cross-generational, structured neuro records. Brainlab and Medtronic are per-case surgical planning tools; they do not follow the patient over years and they certainly do not link relatives. Hospital EMRs do records but not imaging-derived quantification. **The gap between "the imaging quantification" and "the longitudinal structured record" is real and unoccupied.**

**Action:** Promote this from a footnote to a core pillar. A neuro-specific longitudinal patient record with a genogram, comorbidity graph, structured history, cognitive scores over time, and imaging-derived measurements plotted on the same timeline is *genuinely novel enough for an FYP*, technically achievable, and clinically wanted.

---

<a id="hole-7"></a>

### Hole 7 — Simulation is described but not specified, and the honest answer is "not in this FYP"

Your document oscillates between "we modeled everything static" and "we can simulate blood, tissue activity... hormones in blood affect something in the brain." The second is a research programme, not a feature.

What mechanistic simulation actually requires: a neural mass or neural field model, a personalised structural connectome from diffusion MRI, parameter inference (typically Bayesian, MCMC-class), and validation against measured functional data. The Virtual Epileptic Patient pipeline does exactly this — T1 for the structural scaffold, diffusion-weighted MRI for the patient-specific connectivity matrix, neural mass models per region, and MCMC-based inference to fit the patient's seizure organisation. It took roughly a decade and is being evaluated in a 356-patient randomised trial (EPINOV, NCT03643016). A retrospective study of 53 patients reported ~64% precision in identifying epileptogenic regions versus clinical analysis.

You are not going to beat that, and you should not try.

**Action:** Two options, pick one.
- **(a) Cut it.** State in scope that mechanistic simulation is future work, cite TVB/VEP as the reference implementation, and design your data model so a connectome could be attached later. Cleanest.
- **(b) Do a bounded, honest, non-clinical version as a stretch module.** E.g. run a small neural-mass simulation on a public connectome to *demonstrate the architecture can host it*, clearly labelled as a technical demonstration with no clinical claim. Only if you have spare capacity in the final third.

Do **not** attempt (b) before the core is evaluated.

---

<a id="hole-8"></a>

### Hole 8 — Legal and licensing landmines you have not registered

Four specific ones:

1. **MMSE is copyrighted and commercially licensed.** Your interview notes say to integrate MMSE. The MMSE's rights were exclusively licensed to a commercial publisher, and licensed administrations are sold per-use (commonly cited around USD ~1.20–1.30 per administration; packs priced around USD 89 per 50). It has been removed from textbooks and toolkits as a result. **You cannot ship an MMSE implementation in an open-source application.**
   - **MoCA** is also copyrighted, but the publisher permits use, reproduction and distribution by universities, health professionals, hospitals and clinics *without* permission provided it is free to patients; administrator certification is required, and certification is free for students, faculty and academic researchers. This is a workable path for an academic project — but read the current permission terms yourself before you build it in.
   - **Freely usable alternatives** worth investigating: Mini-Cog, SLUMS, and other open-access instruments. NIHSS, mRS, KPS and GCS are generally free to use, but verify each one's terms for your jurisdiction and confirm with your clinician which are actually used locally.
2. **Anatomy asset licensing.** Z-Anatomy is derived from open sources but has specific licence terms and attribution requirements, and — as you have already documented — real anatomical gaps (no cerebral veins, clipped cranial nerves). Both the licence and the gaps must be declared in your report.
3. **Dataset redistribution.** ATLAS, BraTS, OASIS, ADNI and PhysioNet datasets have data use agreements that generally forbid redistribution. If your GitHub repo is public, **derived data and processed cases must not be committed.** Ship a downloader script, not the data.
4. **Regulatory framing.** Anything that influences a clinical decision is, in most jurisdictions, Software as a Medical Device. Pakistan currently has **no enacted comprehensive data protection law** — PECA 2016 (amended January 2025) is a criminal statute, and the Personal Data Protection Bill remains pending as of mid-2026, though its drafts classify health and medical records as sensitive personal data. The absence of a law is *not* permission; your university ethics committee and the hospital's own governance will be the binding constraints, and international norms are what your examiners will expect you to have considered.

**Action:** A short `LEGAL_AND_ETHICS.md` covering: instrument licensing, dataset DUAs, asset licences, de-identification method, ethics approval route, and an explicit non-clinical-use disclaimer shown in the application UI. This takes a day and prevents a very bad viva moment.

---

<a id="hole-9"></a>

### Hole 9 — No integration story, in a domain where integration is the whole game

A neurologist gets scans from PACS. Your system currently expects NIfTI files that someone has already converted and curated. In a real clinic, that gap is the entire product.

Questions you have not answered: How does a study get *into* your application? DICOM import from CD/USB? DICOMweb query/retrieve against a PACS? A watched folder? What happens with a multi-series study (T1, T1-CE, T2, FLAIR, DWI, ADC, SWI) — how do you identify which series is which? (Series descriptions are notoriously inconsistent between scanners and sites.)

Also note from your own notes: **basic imaging includes T1, T2 with contrast, and MRS; DTI and tractography are used.** That is a multi-sequence, multi-modality reality, not a single-volume one.

**Action:** Decide the ingestion story early and make it a headline feature, not plumbing. "Works from a DICOM folder on a USB stick, on a laptop, with no PACS and no internet" is a *much* stronger claim for a Pakistani public-hospital context than any 3D rendering. Look at Orthanc (DICOM server), dcm4che / pydicom / dcm2niix (conversion), and the OHIF/Cornerstone3D stack (web DICOM viewing) before building anything yourself.

---

<a id="hole-10"></a>

### Hole 10 — "Whole human body, all organs" is scope poison

Every sentence in your document that reaches toward the whole body costs you credibility and time. An examiner reading "a complete digital twin per patient... followed by other major organs and later completing the complete human body" will assume you do not understand the size of the problem.

**Action:** One sentence in Chapter 1 as *vision*. Zero sentences anywhere else. Modularity is demonstrated by *architecture*, not by promises — show a plugin interface or an organ-agnostic data model and the point is made far more convincingly.

> **See:** [Build Plan → Rung 1, the body shell](./FYP_Brain_Digital_Twin_Build_Plan.md#rung-1) for how to make the whole-body claim credible with roughly two weeks of work instead of years.

---

<a id="hole-11"></a>

### Hole 11 — The native desktop port is the least differentiated work and may be the wrong priority

You wrote this yourself: *"Desktop app — necessary, but it's the least differentiated risk."* You are right, and yet it is currently absorbing significant planning energy (Qt/C++/VTK vs Rust/wgpu vs Avalonia benchmarking across three machines).

The tension nobody has named: **your existing stack is WebGL-based (Niivue, React Three Fiber). A native rewrite throws away working code and forecloses the cheapest possible VR path (WebXR).** If you ever want the VR demonstration your document describes, staying web-first gets you a Quest 3 demo for a fraction of the effort of a native rewrite plus a native VR integration.

Delivery format is a *packaging* decision. Tauri or Electron gives you an installable desktop app from the existing codebase in days, with offline capability, local file access, and local storage. That is not architecturally elegant, but "elegant" is not the FYP criterion — *evaluated capability* is.

> **Update — see [Build Plan → Stack decision](./FYP_Brain_Digital_Twin_Build_Plan.md#stack-decision).** This hole is substantially resolved by building on the 3D Slicer platform, which *is* a Qt/C++/VTK application. That path keeps the preferred stack, removes the rewrite cost, and changes the calculus below.

**Action:** Push the native-port decision to a later gate, with an explicit trigger: *"We port natively only if we measure a specific performance requirement the web stack demonstrably fails."* Define that requirement (e.g. interactive volume rendering of a 512³ volume at ≥30 fps on a 4 GB-VRAM laptop). Benchmark against it once. If web passes, ship web-in-a-shell and spend the saved months on evaluation and the clinical layer, which are what actually earn marks.

---

<a id="hole-12"></a>

### Hole 12 — The brain/ear split is unresolved and is quietly forking your team

You have: an approved brain POC, an instructor-assigned ear rebuild, and an intention to merge them into one desktop application eventually. Three workstreams, one small team, on a summer break with failing coordination.

**Action:** Force the decision with the instructor (Part 11). Recommended position to argue: **ear is delivered as a separate, self-contained web deliverable that satisfies his instruction, is explicitly out of the FYP's evaluated scope, and shares only the data model and component library with the brain system.** Merging two organ systems into one application during the FYP is unbudgeted work with zero evaluation value.

---

<a id="hole-13"></a>

### Hole 13 — Team and process failure is a bigger risk than any technical problem

Summer break, dispersed team, no coordination, instructor sending mixed signals. Technical plans do not survive this. Process does.

**Action** — minimum viable process, all of it cheap:
- **One repo of record** for documents, versioned, with a decision log (one ADR file per decision: context, options, choice, consequences).
- **Named owner per track** (Part 7). Ownership means "this person answers questions about it," not "this person does all the work."
- **One 45-minute weekly sync**, fixed slot, written agenda, written outcomes. Non-negotiable, even if only two people attend.
- **A written decision memo to the instructor** rather than open-ended questions — see Part 11. Open questions invite open answers; a memo with a recommendation and a request for confirmation produces decisions.
- **Async by default** using your existing Claude Code workflow; keep `CLAUDE.md` and `HANDOFF.md` current so anyone can resume cold.

---

<a id="part-3"></a>

# Part 3 — What already exists, and what it kills

This is the section you asked for most directly: *what is already available that would make this development worthless.* The honest answer is "most of what you described," but the exercise is only useful if it also tells you what is left. Both are below.

<a id="tier-a"></a>

## Tier A — Commercial clinical systems (regulated, expensive, entrenched)

**Brainlab (Elements suite, Cranial Navigation, Curve/Kick platforms).** Automated multimodal image fusion, deformable co-registration, segmentation, white-matter tractography, multi-trajectory surgical approach planning, brain-shift compensation between pre-op and intra-op scans, vascular object generation from CTA/MRA/DSA, and resting-state and task-based fMRI analysis for visualising eloquent cortical areas. Microscope-based AR overlay of planned targets onto the live surgical view. Remote planning over hospital VPN. In use at the majority of top US neurosurgery centres.

**Medtronic StealthStation S8.** Optical and electromagnetic instrument tracking, PACS/DICOM import-export, multimodal fusion, anatomical segmentation, trajectory creation and simulation, and built-in tractography using constrained spherical deconvolution to resolve crossing fibres better than standard DTI — explicitly marketed for exploring safe surgical corridors. Integrates with iMRI, iCT, C-arm, O-arm, microscopes and endoscopes.

**Surgical Theater, ImmersiveTouch (IVSP).** Patient-specific VR reconstruction directly from DICOM for surgical rehearsal, team collaboration and patient education.

> **What this kills:** Any claim to build a surgical planning or neuronavigation system. Every feature in your document's "visualisation to assist further... most importantly for the surgery" paragraph already exists, is FDA/CE cleared, is validated, and — critically, per your own notes — **neuronavigation is already available in Pakistan.** Do not compete here. You would be building an unregulated, unvalidated version of a mature regulated product.

<a id="tier-b"></a>

## Tier B — Research-grade digital twins (the real state of the art)

**The Virtual Brain (TVB) / Virtual Epileptic Patient (VEP) / EPINOV / Virtual Brain Twin.** Personalised whole-brain network models built from a patient's T1 (structural scaffold) and diffusion-weighted MRI (connectivity matrix), with neural mass models per region and Bayesian inference fitting the model to the patient's recorded seizures, in order to estimate the epileptogenic zone network and simulate virtual resection. Validated retrospectively (53 patients, ~64% precision vs clinical analysis) and evaluated prospectively in EPINOV, a 356-patient randomised trial — described as the largest randomised trial ever run in epilepsy surgery. The Horizon Europe **Virtual Brain Twin** project is the successor, extending the approach toward psychiatric conditions and operating through the EBRAINS infrastructure.

**Digital Twin Brain (Fudan).** Whole-brain simulation and assimilation platform; recent work simulates and perturbs functional networks underlying mental illness.

**BrainTwin-AI and similar 2026 work.** Multimodal MRI+EEG cognitive twins combining transformer-based tumour segmentation with EEG-derived state classification.

**The literature's own verdict.** A 2026 systematic scoping review found 36 qualifying studies across six databases, with publications rising sharply since 2023, and Alzheimer's (14) and stroke (12) as the dominant conditions. A parallel 2026 review argues most of these are not true digital twins at all, and that the field is bottlenecked on measurement validity, uncertainty quantification and prospective evaluation.

> **What this kills:** Any claim to novelty in mechanistic brain simulation. But note the *shape* of that last finding — the field's own reviewers say the bottleneck is validation and integration, not more models. That is a hint about where a small team can contribute something real.

<a id="tier-c"></a>

## Tier C — Open-source imaging and computing stack (free, excellent, and you should be standing on it)

| Tool | What it does | Why it matters to you |
|---|---|---|
| **3D Slicer** | Free, BSD-licensed platform: visualisation, segmentation, registration, GPU volume rendering, image-guided procedure planning and navigation, VR via SlicerVR, FreeSurfer import. 2M+ installer downloads. | This is the free version of Tier A. If your app's feature list is a subset of Slicer's, you have no project. |
| **SlicerDMRI** | Diffusion MRI, multi-fibre UKF tractography, interactive tract isolation | Tractography is already free and open. |
| **FreeSurfer / FastSurfer** | Cortical parcellation and surface reconstruction; FastSurfer gives FreeSurfer-conform outputs with whole-brain segmentation in under a minute and full surfaces in about an hour | Do not write your own parcellation. Use this. |
| **SynthSeg** | Contrast- and resolution-agnostic brain segmentation without retraining | Works on messy real-world clinical scans, which is exactly your setting. |
| **nnU-Net** | Self-configuring segmentation framework; wins most challenges; typically needs dataset-specific fine-tuning to generalise | Your realistic path for lesion segmentation. Fine-tune, don't invent. |
| **TotalSegmentator** | Whole-body segmentation, ~104 CT structures / ~56 MR | Relevant if the "other organs" vision is ever pursued. |
| **MedSAM / SAM-2 medical variants** | Promptable segmentation across modalities | Interesting for a human-in-the-loop correction UX. |
| **ITK-SNAP, ANTs, FSL, MRtrix3, dcm2niix** | Segmentation editing, registration, diffusion processing, DICOM→NIfTI | The standard toolchain. Learn it. |
| **Niivue, OHIF, Cornerstone3D, VTK.js** | Web-based medical image viewing and rendering | You already use Niivue. OHIF/Cornerstone is the mature DICOM-web viewer if you need one. |
| **Orthanc, dcm4che** | Lightweight open-source DICOM servers | The realistic answer to "how does data get in without a hospital PACS." |
| **BIDS** | Brain Imaging Data Structure — the community standard for organising neuroimaging datasets | Adopt it. Free credibility, free interoperability, and it forces the discipline you currently lack. |

> **What this kills:** Any plan that involves writing segmentation, registration, parcellation or tractography from scratch. It also kills "we made a 3D brain viewer" as a contribution. **What it gives you:** an enormous free foundation. Your contribution should be *what you assemble on top*, not the components.

<a id="tier-d"></a>

## Tier D — Anatomy atlases and education tools

Complete Anatomy, Visible Body, BioDigital Human, Z-Anatomy (free/open), Kenhub, and every medical school's existing resources.

> **What this kills:** The entire "complete atlas of the human body, interactive, every system named with textbook detail" pillar. This is a mature, well-funded, commodity market. Building it adds zero to your FYP and consumes months.

---

<a id="surviving-gaps"></a>

## So what is actually left?

Four gaps survive the audit. They are not glamorous. They are real.

**Gap 1 — Assembly and longitudinality.** Every tool above does one slice of the problem for one moment in time. Slicer does imaging but not records. EMRs do records but not imaging-derived quantification. Brainlab does one surgical case, not five years of a patient's life. **Nobody puts structured neuro history, family history/genogram, comorbidities, cognitive and functional scores, and imaging-derived quantitative measures on one timeline for one patient over years.** This is your "record-keeping down the generations" idea and it is the strongest thing in your document.

**Gap 2 — Context and cost.** Tier A costs six figures, runs on dedicated hardware, requires hospital IT and PACS integration, and is licensed per seat. Tier C is free but is a researcher's toolkit with a researcher's learning curve and no clinical workflow. **An open, offline-first, laptop-class, no-PACS-required, low-training-burden tool aimed at resource-constrained neurology practice is not covered by either.** Your setting is your advantage here, not your limitation.

**Gap 3 — Structured anatomical-to-clinical mapping.** Taking a lesion mask, attributing it to atlas regions and white-matter tracts, and presenting the *expected* clinical correlates as structured, literature-referenced hypotheses (with explicit uncertainty) is thin territory. Slicer will not do it. Brainlab will not do it. It is bounded, buildable, and evaluable against radiology reports and clinical findings — and it directly serves the neurologist's stated priority of eloquent areas and safe surgery.

**Gap 4 — Explanation and teaching.** Patient/family communication and resident training are chronically under-served, carry far lower regulatory risk, and your neurologist's own comment that software familiarity takes weeks for the experienced and months for beginners tells you learnability is a recognised problem. Your interview questionnaire already flagged medical students as "a second, lower risk user group" — that instinct was correct.

**These four gaps are what your FYP should be about.**

---

<a id="part-4"></a>

# Part 4 — Candidate theses, scored

Four viable reframings. Scored 1–5 (5 = best) on criteria that actually determine an FYP's fate.

**Criteria:** *Feasible* (can a small team finish it) · *Novel* (survives the Part 3 audit) · *Evaluable* (can you prove it worked) · *Data-safe* (works without patient data if procurement fails) · *Clinically wanted* (matches the interview) · *Reuses POC* (your existing code and assets)

| # | Thesis | Feas | Novel | Eval | Data-safe | Wanted | Reuse | **Total** |
|---|---|---|---|---|---|---|---|---|
| **T-A** | **Longitudinal neuro case workstation** — structured record + genogram + scores + imaging-derived quantification on one patient timeline, offline, laptop-class | 4 | 4 | 4 | 4 | 5 | 4 | **25** |
| **T-B** | **Lesion→region→deficit mapper** — automated segmentation, atlas attribution, tract involvement, structured deficit hypotheses with uncertainty | 4 | 4 | 5 | 5 | 4 | 5 | **27** |
| **T-C** | **Teaching twin** — case-based neuroanatomy + disorder learning environment with real cases, for students and residents | 5 | 2 | 4 | 5 | 3 | 5 | **24** |
| **T-D** | **Mechanistic simulation twin** — TVB-style personalised dynamics | 1 | 1 | 2 | 3 | 2 | 2 | **11** |

<a id="thesis-recommendation"></a>

### Recommendation

**Build T-B as the technical core, inside the T-A product frame, with T-C as the demonstration and dissemination layer. Cite T-D as future work.**

Concretely, the FYP is:

> **An open, offline-capable neuro case workstation that ingests a patient's DICOM study, produces quantified and anatomically localised lesion characterisation for ischemic stroke and glioma, attributes involvement to atlas regions and white-matter tracts with explicit uncertainty, presents literature-referenced clinical correlates as hypotheses rather than conclusions, and maintains this alongside a structured longitudinal neuro record — designed to run on a single laptop in a resource-constrained clinical setting with no PACS dependency.**

Why this specific combination works:

- **It matches your interview exactly.** Stroke and glioma are the two most common conditions he named. Imaging is mandatory for both. Eloquent areas were volunteered as a concern. Structured history was emphasised heavily. Missing > over-calling is honoured by presenting hypotheses with uncertainty rather than filtered conclusions.
- **It is evaluable without a hospital.** Segmentation and region attribution can be measured entirely on public datasets. Clinician review is an *enhancement*, not a dependency. This de-risks your single largest procurement risk.
- **It reuses everything you have built.** Niivue, R3F, the disorder mapping, the case data, the anatomy assets.
- **It survives Part 3.** It is not a viewer (Slicer wins), not a navigation system (Brainlab wins), not an atlas (Complete Anatomy wins), and not a simulator (TVB wins). It is the assembly, the longitudinal record, and the structured mapping — the four surviving gaps.
- **It has an honest "digital twin" story.** T1 visualisation plus T2 quantification, with an architecture built to accept T3 mechanistic modelling later. Chapter 1 writes itself.

<a id="non-goals"></a>

> **Build mapping:** how this thesis becomes a demonstrable application is set out in [Build Plan → Rung map](./FYP_Brain_Digital_Twin_Build_Plan.md#rung-map).

### Explicit non-goals (put these in the report)

1. No diagnosis. The system outputs findings and hypotheses; a clinician decides.
2. No intra-operative use, no navigation, no tracking, no registration to a physical patient.
3. No whole-body coverage. Brain only.
4. No mechanistic simulation of brain dynamics.
5. No claim of regulatory clearance; not for clinical use.
6. No general-purpose anatomy atlas.

---

<a id="part-5"></a>

# Part 5 — Requirements skeleton

Not the SRS. The spine you hang the SRS on. Fill this in during Phase 2; it should be ~30–50 pages by submission.

<a id="scope-statement"></a>

## 5.1 Scope statement (one paragraph, memorise it)

Write it in this shape and let every team member repeat it identically:

> *"[System name] is a desktop application for neurologists and neurosurgical teams in resource-constrained settings. It ingests a patient's brain imaging study from local media, computes quantitative and anatomically localised characterisation of ischemic stroke and glioma lesions, maintains a structured longitudinal neurological record including clinical history, family history and standardised scores, and presents imaging-derived measurements and clinical data on a unified patient timeline. It is a decision-support and record-continuity tool. It does not diagnose, does not plan surgery, and is not approved for clinical use."*

<a id="user-stories"></a>

## 5.2 User stories (write 8–12; here are the seed set)

1. As a **neurologist**, at a **follow-up consult**, I need to see **how the lesion volume and affected regions changed since the last scan**, so that I can decide **whether the current management is working**.
2. As a **neurologist**, at **first presentation**, I need to **capture structured history including handedness, comorbidities, family history and obstetric history in under three minutes**, so that **the record is complete and reusable at every later visit**.
3. As a **neurosurgeon**, at **pre-op review**, I need to see **which eloquent regions and white-matter tracts the lesion abuts, with a stated confidence**, so that I can **factor risk into the approach discussion**.
4. As a **neurologist**, at **any visit**, I need to **administer and store a cognitive screening instrument and see the score trend**, so that I can **detect decline objectively rather than by impression**.
5. As a **clinician in a hospital without PACS**, I need to **load a study from a CD or USB with no internet and no server**, so that **the tool is usable where I actually work**.
6. As a **resident**, at **study time**, I need to **step through a real anonymised case from history to imaging to region attribution**, so that I can **build clinical-anatomical correlation**.
7. As a **department**, at **audit time**, I need **an exportable, provenance-stamped record of what the system computed and with which version**, so that **findings are reproducible**.

<a id="functional-requirements"></a>

## 5.3 Functional requirement groups

| Group | Contents |
|---|---|
| **F1 Ingestion** | DICOM folder import; series identification and sequence classification (T1, T1-CE, T2, FLAIR, DWI, ADC, SWI, CT); NIfTI import; de-identification; validation and error reporting |
| **F2 Preprocessing** | Reorientation to canonical space; resampling; bias-field correction; skull stripping; inter-series co-registration; registration to template space; defacing |
| **F3 Analysis** | Lesion segmentation (stroke, haemorrhage, glioma sub-regions); volumetry; atlas-based region attribution; white-matter tract involvement; laterality; comparison to prior study |
| **F4 Visualisation** | 2D orthogonal views with overlays; 3D surface and volume rendering; region highlighting; side-by-side and difference views across timepoints; window/level control |
| **F5 Clinical record** | Demographics incl. handedness; presenting complaint; examination findings; comorbidities; medications; allergies; addiction; occupation; marital status; obstetric history; family history and genogram; standardised scores (GCS, NIHSS, mRS, KPS, and a licence-clean cognitive instrument) |
| **F6 Timeline & comparison** | Unified chronological view of scans, scores, events, medications; trend plots; change detection |
| **F7 Reporting & export** | Structured report generation; measurement export; provenance record; PDF/CSV/JSON output |
| **F8 Safety & governance** | Non-clinical-use disclaimer; uncertainty display on every derived value; audit log; local encryption at rest; no silent auto-filtering of findings |
| **F9 Teaching mode** | Anonymised case library; guided walkthrough; anatomy reference layer |

<a id="nfrs"></a>

## 5.4 Non-functional requirements (make these measurable — vague NFRs get marked down)

- **Performance:** full ingest→analysis→display pipeline for one MRI study in ≤ *X* minutes on a laptop with *specified* CPU/RAM/GPU. Interactive 3D at ≥ 30 fps for a *specified* volume size. **Measure and set X from a baseline run — do not guess.**
- **Offline:** all core functions operate with the network interface disabled. Test this explicitly.
- **Footprint:** installer size and RAM ceiling stated; runs on integrated graphics with a documented degraded mode.
- **Learnability:** a target-user completes a defined core task after ≤ *N* minutes of instruction. Measure it; your clinician's "weeks vs months" comment makes this a legitimate NFR.
- **Reproducibility:** identical input produces identical output; every derived value carries tool version and parameters.
- **Safety:** system never suppresses a candidate finding; over-flagging is preferred to missing, per clinical guidance. Document the operating point you chose and why.
- **Data protection:** encryption at rest; no outbound transmission of patient data by default; de-identification verified by test.

<a id="acceptance-criteria"></a>

## 5.5 Acceptance criteria style

Write every requirement so it can be tested. Bad: *"The system shall accurately segment lesions."* Good: *"For the held-out test split of ATLAS v2.0, the system shall achieve a median Dice coefficient ≥ 0.65 and report per-case Dice, HD95 and ASSD."*

---

<a id="part-6"></a>

# Part 6 — Feasibility

<a id="data-layers"></a>

## 6.1 Data — the layered plan

Your four-layer framing is right. Here it is made concrete, with the two things you actually need to plan around: **what each layer is for**, and **how long it takes to get**.

| Layer | Purpose | Candidate sources | Access friction | Lead time (plan for) |
|---|---|---|---|---|
| **Structural / reference** | Healthy anatomy, template space, parcellation | MNI152 templates; Harvard-Oxford, AAL3, Desikan-Killiany (via FreeSurfer), Destrieux, Schaefer; JHU white-matter atlas; IXI | Mostly open | Days |
| **Disease-specific: ischemic stroke** | Lesion segmentation training/eval | ATLAS v2.0 (chronic lesions, masks); ISLES challenge editions (acute, multimodal) | Registration + form / challenge terms | 1–4 weeks |
| **Disease-specific: haemorrhage** | ICH segmentation/eval | PhysioNet CT-ICH (Hssayeni et al.) | PhysioNet credentialing for some datasets; this one is low friction | Days–2 weeks |
| **Disease-specific: glioma** | Tumour sub-region segmentation | BraTS (current edition), BraTS-Africa | Registration on challenge platform, terms acceptance | 1–3 weeks |
| **Disease-specific: dementia** | Atrophy, longitudinal | OASIS-3/4; ADNI | DUA; ADNI requires an application with a stated purpose | 2–8 weeks |
| **Functional / electrophysiology** | Epilepsy, EEG | CHB-MIT, TUH EEG Corpus | Registration | Days–2 weeks |
| **Connectivity** | Tractography, connectome (only if you go near T3) | HCP; enhanced diffusion collections | DUA; HCP has restricted tiers | 2–8 weeks |
| **Patient-specific (local)** | Real-world validation, the thing that makes the FYP special | Partner hospital, retrospective, de-identified | **Ethics/ERC approval + institutional MoU + hospital IT + consent framework** | **3–6 months, may fail** |

**The critical planning consequence:** the local patient data path is 3–6 months minimum and can fail for reasons entirely outside your control. Therefore:

1. **Start it now, in parallel, as a separate workstream with a named owner.** Your notes mention "MOUs collaborating on Asif Jamal" and a clinic schedule — that thread is the highest-leverage thing anyone on the team can pull this month.
2. **Design the entire evaluation so it completes on public data alone.** Local data becomes a bonus chapter ("external validation on N retrospective local cases"), not a dependency.
3. **The number 300–500 in your notes is a research-study number, not an FYP number.** For a retrospective validation chapter, 20–50 well-characterised local cases with reports is plenty and is roughly 10× easier to obtain.

**Also:** commit to **BIDS** for dataset organisation from day one, and never commit derived patient data to a public repository.

<a id="compute"></a>

## 6.2 Compute

Honest assessment: **you do not need to train large models, and you should not.**

- **Segmentation:** fine-tune nnU-Net on a single consumer GPU, or use pretrained BraTS-lineage models. A 3D full-resolution nnU-Net fold is on the order of a day per fold on a mid-range GPU; five folds is a week of wall time you can run unattended. That is affordable. Training a novel architecture from scratch is not, and would add nothing.
- **Parcellation:** FastSurfer gives you whole-brain segmentation in about a minute and full surfaces in about an hour; SynthSeg handles off-protocol clinical scans. Both are pretrained. Use them.
- **Registration:** ANTs/elastix on CPU, minutes per case.
- **Rendering:** already solved by your WebGL stack.
- **Where you will actually be short:** disk (imaging datasets are large — budget hundreds of GB), and patience during preprocessing runs. Plan a cached, resumable, idempotent pipeline. Your existing "offline precomputation feeding browser rendering" instinct was correct; formalise it.

Your gaming laptop plus the Fedora machine is sufficient. Colab/Kaggle free tiers cover any burst. This is not a bottleneck — do not let it become an excuse.

<a id="skills-gap"></a>

## 6.3 Skills gap

Ranked by how much it will hurt if unaddressed:

1. **Neuroimaging fundamentals** — sequences, what each shows, coordinate conventions (RAS vs LPS), template spaces, registration. **Highest risk of silent catastrophic error.** A lesion in the wrong hemisphere renders every downstream claim false, and nothing in the software will warn you.
2. **Clinical neuroanatomy** — enough to know what a region attribution means and when it is nonsense.
3. **Evaluation methodology** — segmentation metrics, agreement statistics, study design. Without this there is no Chapter 4.
4. **Medical software governance** — SaMD concepts, de-identification, consent, IRB/ERC process.
5. **Clinical HCI** — the 5-minute consultation, alert fatigue, information density.
6. Graphics/rendering, app architecture — **you already have these.** Do not over-invest here; it is the comfortable work, which is exactly why it will absorb time it does not deserve.

<a id="hardware-vr"></a>

## 6.4 Hardware and VR — the honest answer

Your instructor's call (software-only) is correct for the *evaluated deliverable*. But your instinct to explore is also right, and there is a cheap way to honour both.

**What is genuinely cheap for you:** **WebXR.** Your stack is already WebGL. Adding a WebXR session to an existing R3F scene is a small, bounded piece of work — you get a Quest 3 stereoscopic walkthrough of a real patient's segmented brain, with controller-based slicing and region inspection, for a fraction of the effort of any native path. As a *demonstration module* with no clinical claim, this is a strong, low-risk showpiece.

**What is not cheap and you should not attempt:**
- **Haptics.** Force-feedback devices with credible tissue response are the core IP of Tier A simulators (NeuroTouch/NeuroVR, ImmersiveTouch). A gyroscope-and-accelerometer pencil is not haptics; it is tracking without force, which for surgical simulation is close to worthless and will be recognised as such.
- **Physical registration.** Mapping a virtual model to a physical head with clinically meaningful accuracy is the hardest part of neuronavigation and is solved with tracked optical/EM systems. Out of reach.
- **Deformable tissue simulation.** Real-time soft-tissue physics is computationally demanding and is a research field of its own.

> **See:** [Build Plan → Rung 4](./FYP_Brain_Digital_Twin_Build_Plan.md#rung-4) and [Rung 5](./FYP_Brain_Digital_Twin_Build_Plan.md#rung-5) for the phantom-based hardware path that makes a tracked-pointer prototype both honest and measurable.

**Recommended position:** VR is a **stretch module, WebXR-based, in the final third, only after core evaluation is complete**, presented as "the architecture supports immersive review" rather than "we built a surgical simulator." Note the strategic implication for Hole 11: **this argues for staying web-first.** A native rewrite makes your cheapest impressive demo expensive.

---

<a id="part-7"></a>

# Part 7 — The learning and research plan

This is the operational core. It has three components: **phases** (what happens when), **tracks** (what each person learns and owns), and **artifacts** (what exists at the end of each phase). Weeks are relative — anchor Week 1 to whenever you start.

<a id="phases"></a>

## 7.1 Phase structure

<a id="phase-0"></a>

### Phase 0 — Decide (Weeks 1–2)

The goal is to stop the drift. Nothing technical happens.

| Deliverable | Owner | Definition of done |
|---|---|---|
| `VISION_AND_SCOPE.md` | Lead | Contains the one-paragraph scope statement, the T1/T2/T3 twin tier table, and the six non-goals verbatim |
| `NON_GOALS.md` | Lead | Six or more explicit exclusions, each with a one-line justification |
| `DECISIONS/` (ADR folder) | Lead | ADR-001 through ADR-005 written for: thesis choice, brain/ear split, web-vs-native, primary user, cognitive instrument choice |
| Instructor decision memo | Lead | Sent (see Part 11). Recommendation + request for confirmation, not open questions |
| Track ownership assigned | Team | Every track in 7.2 has a named owner |
| Weekly sync scheduled | Team | Fixed slot in calendar, agenda template created |
| Ethics/data access enquiry initiated | Data owner | First email sent to hospital contact and university ERC |

**Gate to Phase 1:** the scope statement is written down and every team member can state it from memory.

<a id="phase-1"></a>

### Phase 1 — Evidence (Weeks 3–7)

Build the knowledge base that justifies every decision in the report.

| Deliverable | Owner | Notes |
|---|---|---|
| `LITERATURE/landscape_review.md` | Research owner | Structured review across the four tiers of Part 3, with an evidence table: system, capability, licence, cost, gap |
| `LITERATURE/digital_twin_definitions.md` | Research owner | The definitional debate; positions your T1/T2/T3 claim in the literature |
| `LITERATURE/segmentation_soa.md` | ML owner | nnU-Net lineage, BraTS/ISLES leaderboard state, what performance is realistic |
| `COMPETITOR_TEARDOWN.md` | Lead | Slicer, Brainlab, StealthStation, ImmersiveTouch, TVB — feature-by-feature vs your proposed scope, with the "why we are not this" column |
| `LEGAL_AND_ETHICS.md` | Governance owner | Instrument licensing, dataset DUAs, asset licences, de-identification, ethics route, disclaimer text |
| Neurologist interview round 2 | Clinical owner | Structured, targeted at the gaps (Part 11.2). Recorded and transcribed |
| Datasets acquired | Data owner | ATLAS, BraTS, CT-ICH, OASIS at minimum, organised in BIDS, download scripted not committed |
| `EVALUATION_PROTOCOL.md` (v1) | Eval owner | Part 9 turned into a specific, executable protocol |

**Gate to Phase 2:** you can answer "why is this not just 3D Slicer?" in two sentences, with citations.

<a id="phase-2"></a>

### Phase 2 — Specify (Weeks 8–12)

| Deliverable | Owner | Notes |
|---|---|---|
| `SRS.md` | Lead | Part 5 fully expanded; every requirement testable |
| `DATA_MODEL.md` | Backend owner | Patient, Study, Series, Derived artifact, Observation, Score, Relative/genogram node. Controlled vocabularies named |
| `IMAGING_PIPELINE.md` | Imaging owner | Every stage, tool, version, coordinate space, and failure mode. Include the registration path diagram |
| `ARCHITECTURE.md` + ADRs | Lead | Module boundaries, the organ-agnostic seam, storage, packaging decision |
| `UX/` wireframes | UX owner | The five core screens. Test on paper with a clinician before building |
| Risk register live | Lead | Part 10, reviewed weekly |

**Gate to Phase 3:** a clinician has looked at wireframes and said something critical about them.

<a id="phase-3"></a>

### Phase 3 — Vertical slice (Weeks 13–22)

**One disorder, end to end, measured.** Recommend **ischemic stroke** first: ATLAS gives you masks, lesions vary in position and size (which your instructor already asked about), CT-ICH gives a second modality, and it is the condition your neurologist named as most frequent.

Order of work, strictly:
1. DICOM ingest → sequence identification → NIfTI conversion → BIDS layout
2. Preprocessing chain, with a QC report per case
3. Segmentation (fine-tuned nnU-Net or pretrained baseline) → **measure Dice/HD95/ASSD immediately**
4. Atlas registration → region attribution → **measure attribution agreement**
5. Visualisation of the above in the existing POC UI
6. Clinical record module + timeline
7. Report export with provenance

**Gate to Phase 4:** you have real numbers in a table for steps 3 and 4. Not screenshots. Numbers.

<a id="phase-4"></a>

### Phase 4 — Broaden and validate (Weeks 23–32)

- Second disorder (glioma via BraTS) through the same pipeline — this is where the architecture proves itself or does not.
- Longitudinal comparison across timepoints (OASIS gives you this without patient data).
- Clinician evaluation sessions (Part 9, items 3 and 4).
- Local retrospective external validation **if and only if** ethics and data landed.
- Optional: WebXR stretch module.
- Packaging, installer, offline verification test.

<a id="phase-5"></a>

### Phase 5 — Write and defend (Weeks 33–38)

Thesis, demo video, viva prep. **Write continuously from Phase 1** — the literature review, competitor teardown, and evaluation protocol are already chapters. If you leave writing to Phase 5 you will lose.

---

<a id="tracks"></a>

## 7.2 Learning tracks

Eight tracks. Each has an owner. Ownership means *this person becomes the team's reference on it and writes that chapter section* — not that they do all the work alone. With a small team, one person may own two.

Budget roughly **6–10 focused hours per track for the foundation**, spread over Phases 0–2, then continuous depth as needed.

---

<a id="track-t1"></a>

### T1 — Clinical neuroanatomy and neurological disease

**Why:** you cannot build region attribution without knowing what a region means, and you cannot talk to a clinician credibly without it.

**Core content:**
- Gross anatomy: lobes, gyri/sulci, deep grey structures, ventricles, brainstem, cerebellum
- Vascular territories: ACA/MCA/PCA — **essential** for stroke, and the single most useful thing to memorise for your chosen thesis
- White matter tracts: corticospinal, arcuate fasciculus, optic radiation, corpus callosum
- Eloquent areas: motor, sensory, language (Broca/Wernicke), visual — and why handedness determines language lateralisation (this is exactly why your neurologist called handedness mandatory)
- Ischemic stroke: pathophysiology, time course, penumbra, imaging appearance over time
- Glioma: grading, growth patterns, the enhancing / non-enhancing / oedema distinction (which is exactly what BraTS labels)
- Clinical scales: GCS, NIHSS, mRS, KPS — what each measures, when used, scoring

**Resources:** a standard neuroanatomy atlas; Radiopaedia (free, excellent, case-based, and the fastest route to radiological pattern recognition); the neuroanatomy chapters of any clinical neurology text; the BraTS challenge papers for label definitions.

**Exercise:** take 10 ATLAS cases. Without any tool, look at the lesion and state the vascular territory and expected deficits. Then check against literature. Your error rate on this is your true starting point.

---

<a id="track-t2"></a>

### T2 — Medical imaging fundamentals and data formats

**Why:** this is where silent, invisible, project-destroying errors come from.

**Core content:**
- MRI sequences: T1, T1-CE, T2, FLAIR, DWI, ADC, SWI, MRS — what each shows and why stroke looks different at hour 3 vs week 3
- CT: windowing, why CT is first-line for haemorrhage
- DICOM: the standard, tags, series vs study, why series descriptions are unreliable across scanners
- NIfTI: header, affine, orientation
- **Coordinate systems: RAS vs LPS, voxel vs world, the affine matrix.** Learn this properly. Left/right flips are the classic disaster.
- Template spaces: MNI152, Talairach; what "normalised to MNI" actually does and what it destroys
- Registration: rigid, affine, deformable; when each is appropriate; what goes wrong with a large tumour present (mass effect breaks normalisation assumptions — a real limitation you must document)
- BIDS specification
- De-identification and defacing

**Resources:** the NIfTI-1 header spec; the BIDS specification (readable, short); dcm2niix documentation; FSL and ANTs registration guides; the SynthSeg and FastSurfer papers.

**Exercise:** take one DICOM study. Convert it, inspect the affine, load in three different tools, and confirm left is left in all of them. Write down how you verified it. Then deliberately break the orientation and see how invisible the failure is.

---

<a id="track-t3"></a>

### T3 — Image computing, segmentation and the open toolchain

**Why:** this is the machinery. Learning it is much cheaper than reinventing it.

**Core content:**
- 3D Slicer: full workflow — load, segment editor, registration, volume rendering, models, SlicerDMRI. **Do this before writing any code.** You will discover half your planned features already exist, which is the point.
- FreeSurfer / FastSurfer: what recon-all produces, what the parcellation files mean
- SynthSeg: contrast-agnostic segmentation for messy clinical data
- nnU-Net: dataset format, planning, training, inference, fine-tuning
- ANTs / elastix: registration in practice
- MRtrix3: diffusion and tractography basics (only if you go near tracts)
- Metrics: Dice, IoU, Hausdorff distance and HD95, average surface distance, volume error and Bland-Altman

**Resources:** 3D Slicer's own tutorials (extensive and free); the nnU-Net repository and paper; FastSurfer documentation; the SlicerDMRI tutorials.

**Exercise:** reproduce a published baseline. Run a pretrained BraTS model on BraTS validation data and compute Dice yourself. If your number is wildly off the published range, your pipeline is broken — and finding that out in Week 10 rather than Week 30 is worth the whole exercise.

---

<a id="track-t4"></a>

### T4 — 3D graphics and rendering for medical data

**Why:** you already have this. The gap is the *medical* specifics.

**Core content:** volume rendering and transfer functions; marching cubes and mesh extraction from labels; mesh decimation and smoothing without destroying anatomical accuracy; multi-planar reconstruction; window/level; overlay blending and colormap choice for clinical use (perceptually uniform, colourblind-safe — this matters); performance for large volumes; WebXR basics if you take the stretch module.

**Resources:** Niivue docs and examples; VTK's volume rendering documentation (concepts transfer even if you stay in JS); Cornerstone3D for the DICOM-web side.

**Exercise:** render the same lesion three ways — 2D overlay, 3D surface, volume rendering — and show all three to a clinician. Ask which one they would actually look at. The answer will probably surprise you and will save you months of building the wrong thing.

---

<a id="track-t5"></a>

### T5 — Application architecture, storage and packaging

**Core content:** local-first data architecture; SQLite vs embedded document store for the clinical record; encryption at rest; audit logging; the organ-agnostic module seam (this is how you honour the "whole body" vision credibly); packaging via Tauri/Electron vs native; offline installer; update strategy.

**Exercise:** write ADR-003 (web-in-shell vs native) with the measurable trigger condition from Hole 11, and run the benchmark that decides it. One benchmark, one decision, done.

---

<a id="track-t6"></a>

### T6 — Evaluation, statistics and study design

**Why:** this is the difference between a demo and an FYP. **Under-invested by almost every student team.**

**Core content:** segmentation metrics and their failure modes (Dice is misleading for tiny lesions — this matters enormously for small strokes); agreement statistics (Cohen's/Fleiss' kappa, ICC); Bland-Altman for volume agreement; sensitivity/specificity/PPV/NPV and why the prevalence matters; ROC and operating point selection — and specifically **why your clinician's "missing is worse than over-flagging" instruction determines where on that curve you sit**; sample size intuition; usability instruments (SUS, NASA-TLX); qualitative methods for expert review (think-aloud, structured rubrics).

**Exercise:** write the results tables for Chapter 4 **now**, with the numbers blank. If you cannot design the empty table, you do not yet know what you are measuring.

---

<a id="track-t7"></a>

### T7 — Regulation, ethics, safety and governance

**Core content:** SaMD concept and risk classification logic; why "decision support" vs "diagnosis" is a legally meaningful distinction; IRB/ERC process at your university; informed consent and waiver-of-consent for retrospective de-identified data; de-identification standards and defacing; the Pakistani legal position (no enacted comprehensive data protection law as of 2026; PECA 2016 as amended; the pending Personal Data Protection Bill treating health data as sensitive) and why that means institutional governance, not law, is your binding constraint; instrument licensing (MMSE/MoCA — see Hole 8).

**Exercise:** draft the ERC application. Even if you never submit it, drafting it forces every unresolved data question into the open.

---

<a id="track-t8"></a>

### T8 — Clinical HCI and workflow

**Core content:** the consultation time budget (your clinician runs clinics Tue/Thu 10–12 — do the arithmetic on patients per hour); cognitive load and information density; alert fatigue and why over-flagging has a real cost even when the clinician says they prefer it (resolve this tension explicitly in your design — the answer is usually *display everything, rank it, never hide it*); uncertainty communication; structured data entry that does not slow the clinician down; learnability as a design target.

**Exercise:** shadow one clinic session if permitted, or reconstruct one minute-by-minute from the interview. Time-box every interaction your app would demand.

---

<a id="track-ownership"></a>

## 7.3 Track ownership template

| Track | Owner | Backup | Chapter section they write |
|---|---|---|---|
| T1 Clinical neuro | | | Background: clinical domain |
| T2 Imaging fundamentals | | | Background: imaging; Methods: data |
| T3 Image computing | | | Methods: pipeline; Related work: tools |
| T4 Graphics | | | Methods: visualisation |
| T5 Architecture | | | Design & implementation |
| T6 Evaluation | | | Evaluation & results |
| T7 Ethics/regulatory | | | Ethics, limitations |
| T8 HCI | | | UX design; usability results |

Fill this in during Phase 0. An empty cell is a risk.

---

<a id="part-8"></a>

# Part 8 — Using your tools deliberately

You have unusual leverage here. Use each tool for what it is actually good at.

<a id="research-briefs"></a>

## 8.1 Deep research / Claude Science — for literature and evidence

Best for: systematic literature synthesis, evidence tables, "what is the current state of X," multi-source comparison. Not for: your specific design decisions, or anything requiring judgement about *your* constraints.

**Give it briefs, not questions.** Four worth running, roughly in this order:

**Brief 1 — Digital twin definitional landscape in neurology.**
> Survey how "digital twin" is defined and operationalised in neurology and neuroimaging from 2022 to present. Identify: competing definitions and their criteria; the distinction between visualisation, statistical/data-driven, and mechanistic twins; documented critiques of definitional inflation; and which published systems meet strict criteria versus which are decision-support relabelled. Produce a comparison table of definitions with source, criteria, and example systems. Focus on review articles and consensus/position papers.

**Brief 2 — Automated lesion characterisation state of the art.**
> Survey automated segmentation and quantification of ischemic stroke lesions and adult gliomas on MRI and CT, 2021 to present. Report: leading methods and architectures; benchmark performance ranges on ATLAS, ISLES and BraTS with the metrics used; known failure modes, especially small lesions and out-of-distribution clinical scans; and the availability of pretrained models suitable for reuse rather than retraining. Include a table of reported Dice ranges by dataset and lesion type.

**Brief 3 — Lesion-to-deficit mapping and eloquent area risk.**
> Survey methods for mapping structural brain lesions to expected functional deficits, including lesion-symptom mapping, atlas-based region attribution, white-matter tract disconnection modelling, and eloquent-area risk assessment in neurosurgical planning. Report the evidence base linking specific lesion locations to specific deficits, the atlases and parcellations used, reported accuracy or agreement, and stated limitations regarding individual variability and mass effect.

**Brief 4 — Clinical decision support in low-resource neurology settings.**
> Survey deployment of imaging-based clinical decision support and neuro record systems in low- and middle-income country settings. Report documented barriers including PACS availability, connectivity, hardware, training burden and maintenance; reported successes and failures; and design characteristics associated with sustained adoption. Include any Pakistan-specific or South Asia-specific evidence.

**Then:** every brief output goes into `LITERATURE/` as a `.md` file with your own critical commentary appended. **Do not paste unread output into the thesis.** Read it, verify the key citations at source, and rewrite in your own words — this is both an integrity requirement and the only way you will actually learn the material.

<a id="claude-code-tasks"></a>

## 8.2 Claude Code — for implementation

Best for: pipeline implementation, repo scaffolding, refactoring, test writing, running long experiments. Keep `CLAUDE.md` and `HANDOFF.md` current (you already do this). Give it the `IMAGING_PIPELINE.md` spec and let it implement against it, rather than describing tasks conversationally.

Highest-value Claude Code tasks for this project, in order:
1. DICOM ingest + sequence classification + BIDS conversion, with a validation report
2. Idempotent, resumable, cached preprocessing pipeline with per-case QC output
3. Evaluation harness that computes Dice/HD95/ASSD and emits the results table automatically
4. Provenance/versioning layer threaded through every derived artifact
5. The clinical record schema and CRUD layer

Note that item 3 before item 5 is deliberate — build the measuring instrument before the features.

<a id="chat-usage"></a>

## 8.3 Chat (this) — for reasoning, critique and drafting

Best for: pressure-testing decisions, drafting documents, preparing interview questions, writing the instructor memo, rehearsing viva answers, converting messy notes into structured specs. Bring it the awkward questions — "is this thesis actually novel," "tear apart our evaluation plan," "what will an examiner attack."

<a id="zotero"></a>

## 8.4 Reference management

Start **Zotero** in Week 1. Every source you read goes in immediately with a note. By Phase 5 you will have 80–150 references and reconstructing them from memory is a week of misery you can avoid for free.

---

<a id="part-9"></a>

# Part 9 — Evaluation plan

**Design this before you build. It is what separates an FYP from a demo, and it is where the marks are.**

<a id="eval-claims"></a>

## 9.1 The claims you will make, and how each is proven

| # | Claim | Method | Data needed | Metric | Clinician needed? |
|---|---|---|---|---|---|
| E1 | The system segments stroke and glioma lesions with performance comparable to published baselines | Held-out test split, standard metrics | ATLAS, BraTS, CT-ICH (public) | Dice, HD95, ASSD, volume error with Bland-Altman | No |
| E2 | The system attributes lesions to anatomical regions in agreement with expert reading | Compare system region output to radiology report / expert annotation | 20–50 cases with reports | Agreement rate, Cohen's kappa, confusion of region categories | Yes |
| E3 | The system detects change across timepoints reliably | Longitudinal test set | OASIS-3 longitudinal, or repeated public scans | Test-retest variability; change detection sensitivity | No |
| E4 | The pipeline runs within stated resource limits offline | Instrumented benchmark on target hardware | Any | Wall time per stage, peak RAM, VRAM, fps, network-disabled pass/fail | No |
| E5 | Clinicians find the output usable and useful | Task-based session + SUS + structured rubric | 5–8 clinicians/trainees | SUS score, task time, completion rate, rubric scores, think-aloud themes | Yes |
| E6 | The structured record is faster/more complete than current practice | Comparison against existing documentation method | Simulated or retrospective cases | Time to complete, field completeness rate | Yes (or trainees) |
| E7 | *(if local data lands)* Performance holds on local retrospective cases | External validation | 20–50 local de-identified cases | Same as E1/E2, reported separately | Yes |

**Note the design property:** E1, E3 and E4 need no clinician and no patient data. If everything external fails, you still have a defensible evaluation chapter. That is deliberate and you should preserve it.

<a id="never-claim"></a>

## 9.2 What you must never claim

- Diagnostic accuracy. You are not running a diagnostic accuracy study and you do not have the design for one.
- Improved patient outcomes. Requires a trial.
- Clinical readiness or regulatory status.
- Superiority to any commercial system. You have not tested one.

<a id="eval-rubric"></a>

## 9.3 Rubric for E5 (draft — refine with your clinician)

For each case reviewed, the clinician scores 1–5:
- The region attribution matched my own reading
- The quantification told me something I would not have easily judged by eye
- The uncertainty presentation was appropriate — neither falsely confident nor uselessly vague
- The longitudinal view would change how I follow this patient
- I would use this in clinic if it were available
- Free text: what is wrong with it

Six items, two minutes per case, and it produces both numbers and quotes for your thesis. Get sign-off on the rubric before you run it.

---

<a id="part-10"></a>

# Part 10 — Risk register

| # | Risk | Likelihood | Impact | Mitigation | Owner |
|---|---|---|---|---|---|
| R1 | Local patient data / ethics approval never lands | High | Medium | Evaluation designed to complete on public data (Part 9); local data is a bonus chapter | Data |
| R2 | Instructor changes direction again mid-project | High | High | Decision memo with written confirmation (Part 11); ADRs record what was agreed and when | Lead |
| R3 | Team coordination fails over break | High | High | Track ownership, weekly sync, async-first, current HANDOFF.md | Lead |
| R4 | Scope creep back toward whole-body / simulation / atlas | High | High | `NON_GOALS.md`; every new feature request tested against a user story | Lead |
| R5 | Silent coordinate/orientation error corrupts all results | Medium | Critical | Explicit orientation verification test in the pipeline; visual QC report per case; T2 exercise | Imaging |
| R6 | Segmentation underperforms; results look bad | Medium | Medium | Use pretrained/fine-tuned models, not novel architectures; report honestly with error analysis — a well-analysed poor result marks better than an unexplained good one | ML |
| R7 | Ear workstream consumes brain workstream capacity | High | High | Formal separation (Hole 12); ear explicitly out of evaluated FYP scope | Lead |
| R8 | Native desktop port consumes months for no evaluated gain | Medium | High | Deferred decision gate with measurable trigger (ADR-003) | Lead |
| R9 | Licensed instrument (MMSE) shipped in open codebase | Medium | High | Licence audit in Phase 1; use a licence-clean instrument | Governance |
| R10 | Dataset DUA breach via public repo | Medium | High | `.gitignore` discipline; downloader scripts only; audit before making repo public | Data |
| R11 | Writing left to the end | High | High | Chapters produced as Phase deliverables from Phase 1 onward | Lead |
| R12 | Clinician becomes unavailable | Medium | Medium | Front-load the round-2 interview; record everything; build a second clinical contact | Clinical |

---

<a id="part-11"></a>

# Part 11 — Questions that force decisions

<a id="instructor-memo"></a>

## 11.1 To the instructor — send a memo, not questions

Open questions have produced inconsistent direction. Send a short memo with a stated recommendation and a request for confirmation. Structure:

> **Subject: FYP scope confirmation — Brain Digital Twin**
>
> Sir, following the POC demonstration and the neurologist interview, we have reviewed what comparable systems already provide and have narrowed our scope. We would like to confirm the following before proceeding to the SRS.
>
> **1. Deliverable.** We propose the FYP deliverable is the brain system only: DICOM ingest, automated lesion characterisation for ischemic stroke and glioma, anatomical region attribution, and a structured longitudinal neurological record, running offline on a laptop. The ear application would be delivered separately as instructed and would not form part of the evaluated FYP scope. **Confirm or redirect.**
>
> **2. Positioning.** We propose positioning the system as decision-support and record-continuity, explicitly not diagnosis, since the interviewed neurologist reported ~99% clinical diagnostic accuracy with imaging contributing ~30% of diagnostic weight. **Confirm.**
>
> **3. Patient data.** We need direction on whether real local patient data will be available, and if so through which institution, since ethics approval and data access have a three-to-six-month lead time. If it is not available, we will evaluate entirely on public datasets. **Please advise on the route and on who should initiate the ethics application.**
>
> **4. Delivery format.** We propose deferring the native desktop rewrite and packaging the existing web codebase as an offline desktop application, unless a measured performance requirement forces a native implementation. This preserves several months for evaluation work. **Confirm or redirect.**
>
> **5. Simulation.** We propose that mechanistic brain simulation is documented as future work rather than attempted, on the basis that the reference implementation in this area is a decade-long programme now in a 356-patient randomised trial. **Confirm.**
>
> **6. Clinical access.** We request a second structured session with the neurologist, and if possible with a neuroradiologist, to close specific gaps in our requirements.

Six confirmations. Each one is a decision he can make in a minute. Keep the answers in writing, in an ADR.

<a id="neurologist-round2"></a>

## 11.2 To the neurologist — round 2

Your round-1 notes have visible gaps (B4, E5 and several sections unanswered). Target these:

**On imaging and reporting**
1. Which exact sequences do you receive for a stroke workup, and for a suspected glioma?
2. Can we see the structure of a standard MRI/CT report — the field template? (Your notes say these have a proper structure; get the real template, not an internet approximation.)
3. Who writes the report, and what does the neurologist do with it?
4. When you look at a scan yourself, what are the first three things you look for?

**On the value proposition — the critical questions**
5. What do you currently measure by eye that you wish were measured numerically?
6. When a patient returns after six months, how do you actually compare the new scan to the old one?
7. What information is routinely missing from a patient's record when they present to you?
8. If a system told you "the lesion involves these regions with this confidence," would that change anything you do? If not, what would?

**On the record**
9. How is family history / genogram currently recorded, and is it ever retrieved later?
10. Which of these do you actually use: GCS, NIHSS, mRS, KPS? Which cognitive instrument is used locally in practice?
11. How long do you have per patient in clinic, realistically?

**On safety**
12. You said missing something is worse than over-flagging. If a tool flagged three possible findings and two were wrong, would you still use it? Where is your tolerance limit?
13. What would make you stop trusting a tool permanently?

**On access**
14. What would it take to get 20–50 retrospective, de-identified cases with reports for validation? Who approves it?
15. Would you be willing to review system output on 10–20 cases and score usefulness on a short rubric?

Questions 5, 6, 7, 8 and 15 are the highest value in the list. If you only get twenty minutes, ask those.

<a id="team-questions"></a>

## 11.3 To the team

1. Who owns each track? (Fill the table in 7.3.)
2. Can everyone state the scope statement from memory?
3. What is the one thing each person will have done by the next sync?
4. What are we no longer doing? (Read `NON_GOALS.md` aloud at every sync for the first month.)

---

<a id="part-12"></a>

# Part 12 — The next fourteen days

Ordered. Nothing technical until day 8.

| Day | Action | Owner |
|---|---|---|
| 1 | Team meeting. Read Part 0 and Part 2 aloud. Argue. Decide the thesis (Part 4). | All |
| 2 | Write `VISION_AND_SCOPE.md` and `NON_GOALS.md`. Assign track ownership. Schedule weekly sync. | Lead |
| 3 | Write and send the instructor decision memo (11.1). | Lead |
| 3 | Send the ethics/data enquiry — university ERC and hospital contact. **This is the long-lead item; it goes out this week regardless of anything else.** | Data |
| 4 | Request neurologist round-2 session. Send the question list in advance. | Clinical |
| 4 | Set up Zotero, `LITERATURE/`, `DECISIONS/` in the repo of record. | Research |
| 5 | Launch deep-research Briefs 1 and 2 (8.1). | Research |
| 5 | Start dataset acquisition: ATLAS, BraTS, CT-ICH registrations submitted. | Data |
| 6 | Draft `EVALUATION_PROTOCOL.md` v1 — the empty results tables from Part 9. | Eval |
| 7 | Weekly sync #1. Review everything above. | All |
| 8–10 | **Install and work through 3D Slicer properly.** Load a real case, segment, register, render. Everyone does this, not just one person. | All |
| 8–10 | T2 exercise: DICOM → NIfTI → verify orientation three ways. Write down the verification method. | Imaging |
| 11–12 | Reproduce a published segmentation baseline and compute Dice yourself. | ML |
| 11–12 | Draft `LEGAL_AND_ETHICS.md` — instrument licensing audit first. | Governance |
| 13 | `COMPETITOR_TEARDOWN.md` first pass, Slicer vs proposed scope. | Lead |
| 14 | Weekly sync #2. **Gate check: can everyone answer "why is this not just 3D Slicer?"** | All |

If day 14 arrives and that question cannot be answered in two sentences, stop and go back to Part 4. Everything else depends on it.

---

<a id="sources"></a>

## Appendix A — Sources consulted

Landscape and definitions:
- *Digital Twins in Neurology Care: Evidence, Limitations, and a Path Forward* — Journal of Integrative Neuroscience, 2026. https://www.imrpress.com/journal/JIN/25/5/10.31083/JIN50563
- *Digital twin for neurological conditions: a systematic scoping review* — Biomedical Engineering Letters, 2026. https://link.springer.com/article/10.1007/s13534-026-00605-9
- *From fragmented neurotechnologies to closed-loop brain health systems* — Frontiers in Bioengineering and Biotechnology, 2026. https://www.frontiersin.org/journals/bioengineering-and-biotechnology/articles/10.3389/fbioe.2026.1904561/full
- *Principles and Operation of Virtual Brain Twins* — IEEE Reviews in Biomedical Engineering, 2026. https://pubmed.ncbi.nlm.nih.gov/40257892/
- *BrainTwin-AI* — Brain Sciences, 2026. https://doi.org/10.3390/brainsci16040411

Mechanistic twins / TVB:
- *Virtual Epileptic Patient* workflow — medRxiv preprint. https://www.medrxiv.org/content/10.1101/2022.01.19.22269404.full.pdf
- *Emerging personalized virtual brain models* — Acta Epileptologica, 2023. https://aepi.biomedcentral.com/articles/10.1186/s42494-023-00128-1
- EPINOV project — INS Marseille. https://ins-amu.fr/epinov
- Virtual Brain Twin project overview. https://openneuroscience.org/Governance/Virtual-Brain-Twin

Commercial systems:
- Brainlab Cranial Planning / Cranial Navigation. https://www.brainlab.com/surgery-products/overview-neurosurgery-products/cranial-planning/
- Medtronic StealthStation S8. https://www.medtronic.com/en-us/healthcare-professionals/products/surgical-navigation-imaging/surgical-navigation-systems/stealthstation-s8-planning-station.html
- *Neuronavigation: Neuroimaging Applied to Neuromodulation and Neurosurgery* — IntechOpen, 2025. https://www.intechopen.com/chapters/1219997
- *Virtual Reality in Neurosurgery: Advancing Training, Education, and Surgical Planning*. https://pmc.ncbi.nlm.nih.gov/articles/PMC12956409/

Open-source toolchain:
- 3D Slicer. https://www.slicer.org/
- SlicerDMRI. https://dmri.slicer.org/
- FastSurfer. https://deep-mi.org/research/fastsurfer/
- *The state of open-source MRI tooling, 2026*. https://askmri.com/blog/state-of-open-source-mri-2026/
- *Comprehensive protocol for mixed reality visualization and navigation using 3D Slicer* — PLOS One, 2026. https://journals.plos.org/plosone/article?id=10.1371%2Fjournal.pone.0343997

Instruments and licensing:
- MoCA permission terms. https://mocacognition.com/permission/
- *Copyright at the Bedside* — on MMSE licensing. https://pmc.ncbi.nlm.nih.gov/articles/PMC4160306/
- *Monetizing the MoCA: What Now?* — JAGS, 2019. https://agsjournals.onlinelibrary.wiley.com/doi/full/10.1111/jgs.16158

Pakistan legal context:
- Data Protection & Privacy 2026 — Pakistan, Chambers Global Practice Guides. https://practiceguides.chambers.com/practice-guides/data-protection-privacy-2026/pakistan
- Pakistan chapter, ICLG Data Protection Laws and Regulations 2026. https://iclg.com/practice-areas/data-protection-laws-and-regulations/pakistan

---

*End of document. Version 1. Revise it — a plan you never edit is a plan nobody is using.*
