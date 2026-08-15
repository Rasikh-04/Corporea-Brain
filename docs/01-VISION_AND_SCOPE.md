# 01 — Vision and scope

<a id="scope-statement"></a>

## Scope statement

Memorise this. Every team member should be able to say it identically.

> BrainTwin Desktop is a desktop application for neurologists and neurosurgical teams in
> resource-constrained settings. It ingests a patient's brain imaging study from local media,
> computes quantitative and anatomically localised characterisation of ischemic stroke and
> glioma lesions, maintains a structured longitudinal neurological record including clinical
> history, family history and standardised scores, and presents imaging-derived measurements
> and clinical data on a unified patient timeline. It is a decision-support and
> record-continuity tool. It does not diagnose, does not plan surgery, and is not approved
> for clinical use.

<a id="twin-tiers"></a>

## Twin tiers, and where we honestly sit

The term "digital twin" is contested and the literature has become hostile to loose usage.
We adopt an explicit three-tier framing and declare our position, which converts our largest
vulnerability (over-claiming) into a strength (conceptual clarity).

| Tier | Name | What it does | Reference systems | Us |
|---|---|---|---|---|
| T1 | Visualisation twin | Patient-specific 3D representation from real scans; lesions localised, structures labelled. No prediction. | 3D Slicer reconstructions, Brainlab Elements rendering | Where we start |
| T2 | Quantitative twin | Adds derived measurement, longitudinal tracking, atlas-based region attribution, population comparison. Predicts statistically, not mechanistically. | Most stroke and Alzheimer's "digital twin" papers | **Where we ship** |
| T3 | Mechanistic twin | Simulates brain dynamics with personalised parameters; supports virtual intervention. | The Virtual Brain, Virtual Epileptic Patient, EPINOV | The vision, out of reach |

**Declared position:** we build T1 to T2, with an architecture designed so a T3 layer could
be attached later. The data model reserves a place for a structural connectome without
requiring one. Nothing in the report claims T3.

<a id="users"></a>

## Users and moments of use

A capability that does not serve a listed moment is out of scope.

| User | Moment | Time available | What they need |
|---|---|---|---|
| **Neurologist** (primary, pending ADR-004) | Outpatient consult, new or returning patient | 5 to 10 minutes | Fast summary. Has anything changed since last visit. Complete structured history. |
| **Neuroradiologist** | Reporting a study | 10 to 30 minutes | Quantification and comparison to prior. Not another viewer. |
| **Neurosurgeon** | Pre-operative review | 30 to 90 minutes | Lesion relative to eloquent regions and tracts. Approach comparison. |
| **Trainee** (secondary) | Study time | Unbounded | Explanation, anatomy, correlation between clinical picture and image. |

The clinic that grounds this project runs Tuesday and Thursday, 10:00 to 12:00. Do the
arithmetic on patients per hour before designing any screen. See
[`08-UI_UX_SPEC.md`](08-UI_UX_SPEC.md).

<a id="value"></a>

## Value proposition

The interviewed neurologist reported clinical diagnostic accuracy near 99 percent, with
imaging contributing roughly 30 percent of diagnostic weight. That single fact invalidates
"AI-assisted diagnosis" as a pitch: there is almost no headroom and enormous risk.

So the value proposition is not diagnosis. It is:

> We do not diagnose. We make the imaging contribution quantitative, spatially explicit and
> longitudinally comparable, and we make the structured clinical record that surrounds it
> complete and reusable.

Four gaps survive the landscape audit and are what this application actually occupies:

1. **Assembly and longitudinality.** Nobody puts structured neuro history, family history and
   genogram, comorbidities, cognitive and functional scores, and imaging-derived quantitative
   measures on one timeline for one patient over years.
2. **Context and cost.** Commercial systems cost six figures and need hospital IT. Open
   research toolkits are free but are researchers' toolkits with researchers' learning
   curves. An offline, laptop-class, no-PACS, low-training-burden tool is covered by neither.
3. **Structured anatomical-to-clinical mapping.** Lesion mask to atlas regions to
   white-matter tracts to literature-referenced expected correlates, with explicit
   uncertainty. Slicer does not do it; Brainlab does not do it.
4. **Explanation and teaching.** Lower regulatory risk, chronically under-served, and a
   legitimate second user group.

<a id="success"></a>

## What success looks like

At submission, in descending order of importance:

1. A results chapter with real Dice, HD95 and ASSD numbers for at least one disorder, plus a
   region-attribution agreement table against expert reading.
2. An application that loads a real DICOM study from a USB stick on a laptop, with the
   network interface disabled, and produces that output end to end.
3. A structured longitudinal record with a timeline that a clinician has criticised at least
   once and that has been changed in response.
4. Every derived value carrying provenance and a stated uncertainty.
5. A demonstration that can be performed twelve minutes end to end, three times, without
   improvisation.

Everything else is upside.

<a id="fidelity"></a>

## Fidelity tiers

Declare the tier a thing was built at, and never claim above it.

| Tier | Meaning | What may be claimed |
|---|---|---|
| **D — Demonstrator** | Works on curated data, in a scripted path, under supervision | "We demonstrate that the architecture supports X" |
| **F — Functional** | Works on arbitrary valid input, handles errors, usable by a non-author | "The system performs X on input of type Y" |
| **V — Validated** | Functional, plus measured against ground truth with reported metrics | "The system performs X with measured accuracy Z" |

<a id="target-profile"></a>

## Target profile at submission

| Rung | What it is | Target fidelity |
|---|---|---|
| R0 | Ingest and spine | **F** |
| R1 | Atlas and body shell | **F** brain, **D** body |
| R2 | Patient mapping, disorders, longitudinal record | **V** |
| R3 | Virtual neuronavigation, planning only | **F** |
| R4 | VR and AR review | **D** |
| R5 | Tracked hardware prototype | **D**, with a real number |
| X | Cross-cutting: QC, eval harness, packaging, teaching mode | **F** |

Only R2 needs to be Validated. That is where the marks are and where the thesis claim lives.

<a id="governing-rule"></a>

## The one governing rule

> Every rung of the ladder must emit at least one number that lands in a results table.

If a rung cannot produce a number, it is a demo feature. Demo features get built last,
cheaply, and are never allowed to consume a month. This rule is what separates an incremental
system with evaluation attached from scope creep with a nice narrative.

---

**Related:** [`02-NON_GOALS.md`](02-NON_GOALS.md) ·
[`07-SRS.md`](07-SRS.md) ·
[`19-RESEARCH_BRIDGE.md`](19-RESEARCH_BRIDGE.md) ·
[research plan Part 4](research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#part-4) ·
[build plan rung map](research/FYP_Brain_Digital_Twin_Build_Plan.md#rung-map)
