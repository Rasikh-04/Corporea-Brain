# 18 — POC inheritance

What the three predecessor repositories actually contain, what carries forward, what is
deliberately dropped, and why. Written now, while the knowledge is fresh, because in month
seven nobody will remember which decision was deliberate.

The three live at `~/Projects/BrainTwin`, `~/Projects/EarTwin` and
`~/Projects/BrainTwin_Native`.

<a id="bt-proved"></a>

## BrainTwin — what it proved

A web-first proof of concept: Next.js 16, React 19, React Three Fiber with Three.js for the
atlas explorer, Niivue for the evidence viewer, Zustand, Tailwind, Vitest and Playwright.
Python offline preprocessing. A `/contract` directory holding JSON Schema, fixtures and a
validator that CI ran on every pull request. Four disorders — glioma via BraTS, ischemic stroke
via ATLAS v2.0, epilepsy via CHB-MIT EEG, Alzheimer's via OASIS — across three evidence
renderers.

It was built to demonstrate capability to an instructor, and it succeeded at that. It proved
three things that matter and that we do not need to prove again:

1. **Mapping can be real rather than decorative.** Affected regions came from an actual
   anatomical atlas intersected with actual patient data, computed in the backend, never from a
   guess about where a disorder "should" appear.
2. **The two-step interaction works.** Explore a normal brain by region, then switch into a
   disorder or a specific case and see the grouped, highlighted changes.
3. **Evidence can be traceable.** Every highlighted region linked back to the real file it came
   from, so a reviewer could verify the claim.

<a id="bt-carries"></a>

## BrainTwin — what carries forward

Not code. Ideas, data assets, and hard-won conventions.

| Carries forward | Where it lands |
|---|---|
| **The contract-first discipline** — a validated shared schema with CI enforcement | [`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md), [`05-DATA_MODEL.md`](05-DATA_MODEL.md), and the manifest validator in CI |
| **`NEEDS_SOURCE` and `TODO(neuro-review)`** as first-class states rather than blanks | CLAUDE.md rule 2, and the UI placeholder requirement |
| **`review_status: pending`** and a visible pending-review banner until sign-off | Data model, and a banner a UI bundle cannot remove |
| **The computed-not-recalled rule** for region involvement | CLAUDE.md rule 3, pipeline Stage 10 |
| **The relational schema** already sketched: Region, Disorder, Case, CaseRegionMapping | Expanded into [`05-DATA_MODEL.md`](05-DATA_MODEL.md) |
| **Z-Anatomy derived meshes** and the Blender-to-glTF pipeline | Organ assets, with `known_gaps` carried across verbatim |
| **The documented atlas gaps** — dural sinuses present, no cerebral veins, cranial nerves clipped at the skull base | The brain manifest's `known_gaps`, surfaced in the UI |
| **The dataset downloaders and the never-commit-data posture** | `scripts/`, and the pre-publication audit checklist |
| **The precompute-not-compute-live instinct** | The cached, idempotent, resumable pipeline |

<a id="bt-dropped"></a>

## BrainTwin — what is dropped, and why

| Dropped | Why |
|---|---|
| The entire Next.js and React front end | Different architecture, different platform. See [ADR-003](DECISIONS/ADR-003-application-shell.md). This is a rebuild, not a port. |
| Niivue as the imaging viewer | Slicer's own views replace it, with volume rendering, MPR and transfer functions we would otherwise reimplement |
| Supabase and any hosted backend | The product is offline and single-machine by design |
| Static JSON as the data layer | Correct for a POC with no runtime backend. Wrong for a longitudinal record that must be queried, versioned and encrypted |
| Epilepsy and Alzheimer's as scoped disorders | Scope narrowed to stroke and glioma, the two the clinician named as most common. EEG in particular is a different modality with a different pipeline |
| The two-WebGL-context dance | An artefact of running Three.js and Niivue side by side. Slicer has one render layer |

**The POC is not deleted and it is not a failure.** It is the credibility anchor that got the
project approved, it is cited in the report as prior work, and it may yet serve as the VR
viewer per [ADR-009](DECISIONS/ADR-009-web-poc-disposition.md).

<a id="et-patterns"></a>

## EarTwin — patterns worth stealing

EarTwin is a separate deliverable and stays separate
([ADR-002](DECISIONS/ADR-002-brain-ear-split.md)). But it solved three problems better than
BrainTwin did, and those solutions transfer.

<a id="et-identity"></a>

### The two-tier identity model

Every case is real, from two sources with two audiences, and **the split between them is
identification, not clinical content.** The clinical picture of every case is public; the name
attached to it is not.

Crucially: **de-identification is a projection, not a deletion.** Both copies are produced by
one offline script from one source through two projections. The public projection generalises
date of birth to an age band, drops name, parent names, address, city, facility and phone, and
drops or human-reviews free-text fields because prose carries identifying detail. And the
reasoning is explicit: across a small cohort, date of birth plus city plus facility plus a named
syndrome re-identifies someone on its own, so name removal alone is insufficient.

**All code that knows identities exist lives behind one route.** It checks the session, decrypts
one case's identity blob, returns fields for that one case, never a list, never at build time.
If the identity set outgrows the current storage, one file changes and nothing else does.

This is now [`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md) and the
identity seam in [`05-DATA_MODEL.md`](05-DATA_MODEL.md).

<a id="et-rules"></a>

### The derived-rule pattern

EarTwin's predecessors mapped seventeen clinical findings and zero disorders. EarTwin kept the
findings as an input layer and **derived named conditions on top of them**, through an explicit
rule catalog where each rule declares `required_inputs`, `logic`, `confidence`, `citations` and
a `caveat`.

Three properties of that design transfer directly to the deficit-hypothesis layer:

1. **`required_inputs` and `INSUFFICIENT_INPUT`.** If a case is missing a required input the
   rule does not fire and does not fail; the engine records `INSUFFICIENT_INPUT`. **A rule never
   substitutes a weaker proxy for a missing input.** This is now the pipeline failure taxonomy
   and a coding standard.
2. **`citations` is never empty.** A rule with no source carries the literal `NEEDS_SOURCE` and
   does not ship. This is now enforced by schema on `DeficitHypothesis`.
3. **Confidence is three named bands, not a number**, with `high` meaning direct observation of
   the thing itself and `moderate` meaning a well-established indirect measure. This is now the
   uncertainty display rule.

The honest framing of a limitation also transfers. EarTwin found that NHANES has no bone
conduction data in any cycle, which makes the air-bone gap uncomputable, which makes
conductive-versus-sensorineural classification impossible from that source — and rather than
approximating, it structured the entire rule set around declared input requirements. That is
exactly the posture the mass-effect caveat needs in
[`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md).

<a id="et-atlas"></a>

### Atlas coverage discovered from geometry, not from descriptions

An early EarTwin discovery document claimed the atlas held every needed structure "down to the
individual limbs of the stapes." It did not. That claim came from reading Z-Anatomy's
description files, which name structures that exist only as **label leader lines** — text
anchors, not surfaces. An inventory pass over the actual geometry produced a generated coverage
document listing every absent structure, the reason, and what its absence costs the product.

**Rule adopted:** inventory the geometry, never the description files. Every absent structure is
recorded with a reason and a consequence, and where a disorder's primary site has no geometry
the highlight is substituted onto the nearest exported structure with the substitution recorded
in the case file. This is now a hard requirement in
[`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md) and a field in the attribution result.

<a id="bn-established"></a>

## BrainTwin_Native — what the benchmark established

A genuinely well-built comparison harness. Three candidate stacks — Qt with C++ and VTK, Rust
with wgpu, Avalonia on .NET — against one matched brain-visualisation task, with a single flat
28-column result schema, a byte-identical shared scene, and a report tool that is the only code
permitted to read the results file so a number in a write-up cannot drift from a number on
screen.

**Established:**

- Tier 0, the Hello World control isolating toolchain overhead from rendering, complete on all
  three stacks at 40 runs each.
- Tier 1 complete for Rust with wgpu across the full matrix: it passes 60 fps average, p95 under
  20 ms and p99 under 33 ms on every cell with a real GPU, including the constrained 4 GB
  throttled-CPU cell. The software-rasteriser cell fails at about 4 fps, which is a finding
  about the workload — this task needs a GPU — rather than about any candidate.
- Real methodological findings: GPU device selection falls back silently on an unmatched PCI
  id; absolute timings are comparable only within one capture batch, with roughly 1.8x
  cross-batch drift and no identified cause; the viewport background is part of the measurement
  because a raycast composites it into every non-opaque pixel.
- A working evaluator bundle for a machine with no compiler and no SDK.

<a id="bn-gap"></a>

## BrainTwin_Native — the honest gap in the Tier 1 evidence

**Tier 1 was never completed for Qt+VTK or Avalonia.** The results file holds 56 Tier 1 rows for
Rust, one for Qt+VTK, and zero for Avalonia.

So: **the Qt decision was not made on completed Tier 1 evidence.** Say this in the report. It is
not a weakness of the decision; it is a weakness of the evidence, and the decision rests on
other grounds that are stronger anyway.

<a id="qt-restated"></a>

## The Qt decision, restated

Qt with C++ and VTK is the stack, and the application shell is a custom 3D Slicer application.
The reasoning, in the order that carries weight:

1. **3D Slicer is itself a Qt/C++/VTK application.** The intended stack, the imaging toolchain
   and the open-source foundation converge on one answer. This is not a compromise between
   three options; it is the option that makes the other two irrelevant.
2. **What the platform supplies for free** — DICOM handling, Segment Editor, registration
   modules, volume rendering, markups, scene serialisation, installers, and a module
   architecture that *is* the organ plugin system — is most of R0 and R1.
3. **Tier 0 plus imaging ergonomics.** The absence of any medical volume-rendering template for
   Rust was itself a recorded finding, and it is exactly the "data and math ergonomics"
   criterion the benchmark set out to test.
4. **Team learnability and ecosystem.** Python scripted modules mean the whole team can
   contribute on day one, without waiting for anyone to learn C++.

Full record: [ADR-003](DECISIONS/ADR-003-application-shell.md). What is honestly *not* claimed:
that Qt beat Rust on measured Tier 1 rendering performance. Rust passed Tier 1 and Qt was never
completed. Rendering performance was not the deciding criterion, and the report should say
which criterion was.

<a id="migration"></a>

## Migration table

| Asset | From | To | Action |
|---|---|---|---|
| Z-Anatomy derived brain meshes | BrainTwin `frontend/public/assets/atlas/` | `organs/brain/assets/` | Convert, re-verify orientation, record `known_gaps` |
| DK plus aseg label map in MNI | BrainTwin `data/derived/` | `organs/brain/parcellations/` | Re-verify against ADR-006 before use |
| Dataset downloader scripts | BrainTwin `download/` | `scripts/` | Port, keep the never-commit-data posture |
| Mask-to-atlas overlap logic | BrainTwin `backend/lesion_overlap.py` | `pipeline/attribution/` | **Rewrite, do not port.** The requirements changed: ranked output, uncertainty statement, substitution recording |
| Contract validator pattern | BrainTwin `contract/validate.py` | `scripts/validate_organs.py` | Reimplement against the manifest schema |
| Benchmark harness | BrainTwin_Native `harness/` | `bench/` | Reuse largely as-is. See [`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md) |
| Shared scene assets | BrainTwin_Native `assets/` | `bench/assets/` | Keep. Useful as a rendering fixture |
| Machine baseline record | BrainTwin_Native `docs/04` | `bench/machines/` | Keep verbatim |
| Rule engine pattern | EarTwin `backend/derive/rule_engine.py` | `pipeline/hypotheses/` | Reimplement for region-to-deficit. Keep `INSUFFICIENT_INPUT` |
| Identity route pattern | EarTwin `app/api/identity/` | The identity seam in the record store | Reimplement natively. Keep the single-seam property |

<a id="never-again"></a>

## What must not be resurrected

- **Two rendering contexts fighting for the GPU.** An artefact of the web POC's architecture.
- **Static JSON as the persistence layer** for a longitudinal, encrypted, queryable record.
- **A second full codebase.** If a viewer exists it is thin, exported-to, and holds zero
  analysis logic.
- **Scope beyond stroke and glioma** without an ADR that names what is traded out.
- **Build artifacts committed to git.** The benchmark repository has `stacks/qt-vtk/tier1/build/`
  checked in. Do not copy that pattern.
- **Re-running the stack comparison.** It is closed. Reopening requires new measured evidence
  against a stated criterion, not a preference.

---

**Related:** [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md) ·
[`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md) ·
[ADR-003](DECISIONS/ADR-003-application-shell.md) ·
[ADR-009](DECISIONS/ADR-009-web-poc-disposition.md)
