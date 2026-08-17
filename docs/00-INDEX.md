# 00 — Documentation index

Every document in this set, with every top-level section listed, so a person or an agent can
grep this one file and know exactly where to go. Numbering is stable. Renumbering requires
updating this file and is a review item.

**Conventions used throughout.** "R0…R5" are the build plan's rungs. "E1…E7" are the research
plan's evaluation claims. "F1…F9" are the functional requirement groups in the SRS.
"D / F / V" are the fidelity tiers: Demonstrator, Functional, Validated.

---

## Reading orders

| If you are… | Read, in this order |
|---|---|
| New to the project | README · 01 Vision · 19 Research bridge · 03 Architecture · 18 POC inheritance |
| Starting to code | CLAUDE.md · 03 Architecture · 15 Build and environment · 14 Coding standards · 16 Testing |
| Writing the pipeline | 06 Imaging pipeline · 05 Data model · 10 Evaluation protocol · ADR-006 |
| Designing a screen | 08 UI/UX spec · 09 UI bundle spec · 05 Data model |
| Preparing for viva | 19 Research bridge · CONTRIBUTIONS · 10 Evaluation protocol · 21 Risk register |
| Managing cost and context | 20 AI workflow · ai-workflow A1 · A2 · A3 |

---

## The documents

### [`01-VISION_AND_SCOPE.md`](01-VISION_AND_SCOPE.md)
The scope statement, the twin-tier framing, the users and their moments of use.
Sections: Scope statement · Twin tiers T1 T2 T3 · Primary and secondary user · Moments of use ·
Value proposition · What success looks like · Fidelity tiers · Target profile at submission ·
The one governing rule.

### [`02-NON_GOALS.md`](02-NON_GOALS.md)
What we are explicitly not building, each with a justification, so scope creep has to argue
against a written record.
Sections: The six declared non-goals · Deferred not refused · Things that look in scope and
are not · How to use this in a review · Change procedure.

### [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md)
The layered architecture of the custom Slicer application, the module inventory, and how the
whole-body claim becomes structural rather than rhetorical.
Sections: Layer diagram · Platform layer · Application shell · Body layer · Organ modules ·
Core services · Module inventory and ownership · Module type policy ·
Data flow for one case · Threading and long-running work · Extension dependencies ·
What we never modify upstream · Seams that must not be crossed · Deployment shape ·
How this survives the "what did you actually build" question.

### [`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md)
The organ module contract: the manifest every organ declares and the interface the body
layer calls.
Sections: Why a contract exists · Manifest schema · Field reference · Implementation levels ·
The known_gaps field and why it is load-bearing · Required capabilities per level ·
Registration and discovery · UI obligations of a module · Validation ·
Worked example brain · Worked example ear · Worked example stub.

### [`05-DATA_MODEL.md`](05-DATA_MODEL.md)
Patient, Study, Series, DerivedArtifact, Observation, Score, Relative. Types, units,
vocabularies, provenance, identity, storage.
Sections: Principles · Entity overview · Patient · Study and Series · DerivedArtifact and
provenance · Segmentation and Attribution results · Observation and Score · Relative and
genogram · Controlled vocabularies · Identifiers and de-identification ·
Units and coordinate conventions · Storage and encryption at rest · Audit log ·
Export shapes · Migration policy.

### [`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md)
Every pipeline stage, the tool behind it, the coordinate space at each step, and the failure
mode for each.
Sections: Pipeline overview · Stage 0 ingest and sequence classification ·
Stage 1 conversion and BIDS layout · Stage 2 de-identification and defacing ·
Stage 3 reorientation and resampling · Stage 4 bias-field correction ·
Stage 5 skull stripping · Stage 6 inter-series co-registration ·
Stage 7 template registration · Stage 8 parcellation · Stage 9 lesion segmentation ·
Stage 10 region attribution · Stage 11 tract involvement · Stage 12 deficit hypotheses ·
The orientation assertion · Caching, idempotence, resumability · Per-case QC report ·
Failure taxonomy · Mass effect and the normalisation caveat.

### [`07-SRS.md`](07-SRS.md)
User stories, functional requirement groups F1 to F9, measurable non-functional
requirements, acceptance criteria style, traceability.
Sections: Purpose and audience · Users and moments · User stories US-01 to US-12 ·
F1 Ingestion · F2 Preprocessing · F3 Analysis · F4 Visualisation · F5 Clinical record ·
F6 Timeline and comparison · F7 Reporting and export · F8 Safety and governance ·
F9 Teaching mode · Non-functional requirements · Acceptance criteria style ·
Traceability matrix.

### [`08-UI_UX_SPEC.md`](08-UI_UX_SPEC.md)
Function-first interface specification: screens, information architecture, task flows,
interaction contracts, and the safety rules governing how uncertainty is displayed.
Sections: The design position · Screen inventory · Information architecture ·
Navigation model · S1 Case list · S2 Ingest and QC · S3 Body shell · S4 Brain atlas ·
S5 Case workspace · S6 Attribution and hypotheses · S7 Timeline · S8 Trajectory planner ·
S9 Report and export · S10 Teaching mode · Interaction contracts ·
Uncertainty and confidence display rules · Alerting and the rank-never-suppress rule ·
Error, empty and loading states · Keyboard and accessibility floor ·
Density and the five-minute consult · What is deliberately not designed yet.

### [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md)
The theming seam: how visual identity is packaged as a swappable bundle so functionality
ships first and appearance is polished later without touching module code.
Sections: The seam and the rule that defines it · Bundle anatomy · tokens.json schema ·
Qt stylesheet generation · Layout presets · Icon set ·
Colormap policy for clinical overlays · What a bundle may and may never change ·
Loading and switching bundles · The default bundle · Bundle lint · Open questions.

### [`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md)
How every claim gets proved: the harness, the metrics, the empty results tables, the
clinician sessions.
Sections: The ordering rule · Claims E1 to E7 · Metric definitions and their failure modes ·
The harness as a shipped component · Datasets and splits · Empty results tables ·
Region-attribution agreement protocol · Expert review rubric · Usability protocol ·
Statistical treatment · Reporting rules and what must never be claimed.

### [`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md)
Performance and resource requirements, and how the inherited BrainTwin_Native harness is
repurposed to measure them.
Sections: What the harness already proves and what it does not ·
The batch-comparability constraint · Schema carried over and extended ·
Metrics added for the application · Test matrix for the Qt app · Reference machine ·
Pass and fail criteria · Cold start, footprint, installer size ·
The offline verification test · Running a measurement · Reporting.

### [`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md)
Threat model, PHI handling, encryption, audit, offline posture.
Sections: Threat model · Data classification · De-identification as a projection ·
Defacing · Encryption at rest · Key handling · Access control and the single identity seam ·
Audit log requirements · Network posture · Logging hygiene · Incident procedure ·
Out of scope, stated.

### [`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md)
Licences, data use agreements, instrument rights, regulatory framing, ethics route.
Sections: Component licence register · Dataset agreement register · Atlas and asset
licences · Clinical instrument licensing and the MMSE problem · Regulatory framing ·
Jurisdiction and why institutional governance binds · Ethics approval route ·
Consent for retrospective de-identified data · The in-application disclaimer ·
Attribution obligations · Pre-publication audit checklist.

### [`14-CODING_STANDARDS.md`](14-CODING_STANDARDS.md)
C++, Python, CMake, and Slicer-specific conventions.
Sections: Language versions and toolchains · C++ rules · VTK and Qt object lifetime ·
Python rules for scripted modules · MRML node conventions · Naming ·
Error handling and the no-silent-failure rule · Logging levels · CMake conventions ·
Third-party code policy · Review checklist.

### [`15-BUILD_AND_ENVIRONMENT.md`](15-BUILD_AND_ENVIRONMENT.md)
From a clean machine to a running custom Slicer application.
Sections: Machine requirements and the honest disk and RAM cost · Fedora · Ubuntu ·
Windows · The Slicer superbuild · Watching a running superbuild ·
PythonQt wrapper generation on Qt 6 ·
Static curl and libidn2 · Building the custom application ·
Building one module without rebuilding Slicer ·
ccache · Common build failures · Python environment for the pipeline ·
Verifying the install · When a machine differs.

### [`16-TESTING_STRATEGY.md`](16-TESTING_STRATEGY.md)
Test layers, what each is for, and the tests that are non-negotiable.
Sections: The test pyramid here · Unit tests · Module tests in Slicer ·
Pipeline integration tests · The orientation assertion test · Golden-case regression ·
Evaluation harness tests · UI smoke tests · The offline test ·
Performance regression gate · CI layout · Coverage targets and where they do not apply.

### [`17-RELEASE_AND_PACKAGING.md`](17-RELEASE_AND_PACKAGING.md)
Installers, versioning, offline verification, what ships to a clinician's laptop.
Sections: Release artifacts · Versioning · What goes in the installer and what never does ·
Offline verification as a release gate · Per-platform packaging · Signing, honestly ·
Update strategy · Rollback · Release checklist · The demo build.

### [`18-POC_INHERITANCE.md`](18-POC_INHERITANCE.md)
What the three predecessor repositories contain, what carries forward, what is dropped.
Sections: BrainTwin what it proved · BrainTwin what carries forward ·
BrainTwin what is dropped · EarTwin patterns worth stealing ·
EarTwin the two-tier identity model · EarTwin the derived-rule pattern ·
BrainTwin_Native what the benchmark established ·
BrainTwin_Native the honest gap in the Tier 1 evidence · The Qt decision restated ·
Migration table · What must not be resurrected.

### [`19-RESEARCH_BRIDGE.md`](19-RESEARCH_BRIDGE.md)
**The short connective document.** How each software artifact maps to a research claim, a
build rung, and a thesis chapter, so nothing built is orphaned from the thesis.
Sections: The two source documents · The one governing rule · Rung to document map ·
Document to claim map · Document to chapter map · Gates and their evidence ·
Where the plans and this set disagree, and which wins · How to keep the three in sync.

### [`20-AI_WORKFLOW_AND_COST.md`](20-AI_WORKFLOW_AND_COST.md)
How the team uses Claude Code and Cowork on this project without burning budget or context.
Sections: Why this is a project document · The three annexes · Depth levels ·
The filter-before-escalate rule · Fan-out policy · Compaction checkpoints ·
Scheduled local jobs · What is not set up yet.

### [`21-RISK_REGISTER.md`](21-RISK_REGISTER.md)
Risks, likelihood, impact, mitigation, owner, trigger.
Sections: How to use this register · Technical risks · Project risks ·
Clinical and data risks · Kill criteria summary · The fallback scope · Weekly review.

### [`22-GLOSSARY.md`](22-GLOSSARY.md)
Sections: Clinical terms · Imaging terms · Coordinate and space terms · Platform terms ·
Project terms · Metric definitions · Abbreviations.

### [`CONTRIBUTIONS.md`](CONTRIBUTIONS.md)
The running list of every original component, maintained from day one.
Sections: The contribution sentence · Original modules · Original algorithms ·
Original data structures · Original evaluation instruments · Configured, not built ·
Adopted unchanged.

---

## Decision records — [`DECISIONS/`](DECISIONS/)

| ADR | Title | Status |
|---|---|---|
| [ADR-000](DECISIONS/ADR-000-template.md) | Template | n/a |
| [ADR-001](DECISIONS/ADR-001-thesis-scope.md) | Thesis scope and the surviving claim | Accepted |
| [ADR-002](DECISIONS/ADR-002-brain-ear-split.md) | Brain and ear are separate deliverables | Accepted |
| [ADR-003](DECISIONS/ADR-003-application-shell.md) | Application shell is a custom 3D Slicer app | Accepted |
| [ADR-004](DECISIONS/ADR-004-primary-user.md) | Primary and secondary user | Open |
| [ADR-005](DECISIONS/ADR-005-cognitive-instrument.md) | Cognitive instrument selection | Open |
| [ADR-006](DECISIONS/ADR-006-coordinate-space-and-atlas.md) | Canonical coordinate space and parcellation atlas | Open, blocking |
| [ADR-007](DECISIONS/ADR-007-record-store.md) | Record store technology | Open |
| [ADR-008](DECISIONS/ADR-008-ui-bundle-seam.md) | UI bundle seam, visual design deferred | Accepted |
| [ADR-009](DECISIONS/ADR-009-web-poc-disposition.md) | Disposition of the web POC | Accepted |
| [ADR-010](DECISIONS/ADR-010-slicer-pinned-revision.md) | Slicer superbuild pinned to v5.12.3 | Accepted |

---

## Annexes — [`ai-workflow/`](ai-workflow/)

| File | Contents |
|---|---|
| [A1](ai-workflow/A1-MODEL_ROUTING_AND_COST.md) | Model routing table, local filtering commands, prompt caching, budget tracking, depth levels |
| [A2](ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md) | Measured context surface, DAILY/LIBRARY/REMOVE lists, audit procedure, compaction checkpoints, CLAUDE.md ceilings |
| [A3](ai-workflow/A3-PARALLELISM_AND_BENCHMARK_AUTOMATION.md) | Fan-out decision rule, worktree collision surfaces, harness repurposing, scheduled local jobs |

## Source plans — [`research/`](research/)

| File | Contents |
|---|---|
| [Research plan](research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md) | Landscape audit, surviving gaps, thesis scoring, requirements skeleton, learning tracks, evaluation plan, risk register |
| [Build plan](research/FYP_Brain_Digital_Twin_Build_Plan.md) | The six-rung ladder, stack decision, fidelity tiers, timeline, demo script, chapter mapping |
