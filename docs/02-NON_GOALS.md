# 02 — Non-goals

The purpose of this document is procedural. When someone proposes a feature, it has to argue
against a written record rather than against a person's memory of a meeting. Read it aloud at
the weekly sync for the first month.

<a id="the-six"></a>

## The six declared non-goals

These go verbatim into Chapter 1 of the thesis.

**1. No diagnosis.**
The system outputs findings and hypotheses. A clinician decides. Justification: the
interviewed neurologist reported diagnostic accuracy near 99 percent with imaging carrying
roughly 30 percent of diagnostic weight. A diagnostic aid pitches into a one percent gap in a
domain where errors are catastrophic. There is no headroom and enormous risk.

**2. No intra-operative use, no navigation, no tracking against a physical patient.**
Justification: this is a regulated, validated, entrenched product category (Brainlab
Elements, Medtronic StealthStation), and per the clinical interview neuronavigation is
already available in Pakistan. Building an unregulated version of a mature regulated product
is worse than useless. R3 is pre-operative trajectory planning on imaging only. R5 is a
measurement demonstrator against a 3D-printed phantom with known fiducials.

**3. No whole-body coverage.**
Brain implemented to depth; ear shallow; a small number of stubs. Justification: every
sentence reaching toward the whole body costs credibility and months. Modularity is
demonstrated by architecture, not by promises. See
[`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md), which is how the claim is made
structurally instead of rhetorically.

**4. No mechanistic simulation of brain dynamics.**
Justification: the reference implementation (The Virtual Brain, Virtual Epileptic Patient) is
a decade-long programme now running a 356-patient randomised trial, requiring neural mass
models, a personalised diffusion-derived connectome, and Bayesian parameter inference. Cited
as future work. The data model reserves a place for a connectome without requiring one.

**5. No claim of regulatory clearance. Not for clinical use.**
Justification: anything influencing a clinical decision is Software as a Medical Device in
most jurisdictions. The disclaimer is shown in the application UI, not only in the report.
Text in [`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md).

**6. No general-purpose anatomy atlas.**
Justification: Complete Anatomy, Visible Body, BioDigital and Kenhub are a mature,
well-funded commodity market. The atlas layer exists to give patient findings an anatomical
frame, not to compete as a learning product. Specifically: we never author anatomy prose. We
link out.

<a id="deferred"></a>

## Deferred, not refused

These are legitimate and are simply not in this cycle. They are documented as designed but
not built, with the design included, so they read as scope discipline rather than as gaps.

| Item | Why deferred | Where the design lives |
|---|---|---|
| Additional disorders beyond stroke and glioma | Two disorders at Validated fidelity beats five at Demonstrator | [`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md) |
| Intracerebral haemorrhage on CT | Third disorder; add only if R2 is Validated early | [`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) |
| Diffusion processing and tractography generation | SlicerDMRI exists; we consume a tract atlas, we do not compute tracts | [`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) Stage 11 |
| DICOMweb query and retrieve against a PACS | The target setting has no PACS; local media is the headline claim | [`07-SRS.md`](07-SRS.md) F1 |
| Multi-user, networked or server deployment | Offline single-laptop is the differentiator, not a limitation | [`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md) |
| Full visual design system | Function first; visual identity ships as a swappable bundle | [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md), [ADR-008](DECISIONS/ADR-008-ui-bundle-seam.md) |
| Force-feedback haptics | Actuated device plus tissue model; the core intellectual property of commercial simulators | [`21-RISK_REGISTER.md`](21-RISK_REGISTER.md) |

<a id="looks-in-scope"></a>

## Things that look in scope and are not

The dangerous category. Each of these has been proposed at least once and each would consume
a month for no evaluated gain.

- **Writing anatomy descriptions for structures.** A bottomless pit. Complete Anatomy has a
  team on it. Link to external references. If someone is authoring anatomy prose for more
  than a few days, stop them.
- **Building a better DICOM viewer.** Slicer already is one. Our contribution sits above the
  viewer, not inside it.
- **Writing our own segmentation, registration or parcellation.** nnU-Net, ANTs and Elastix,
  FastSurfer and SynthSeg exist and are better. Fine-tune, do not invent.
- **A second full codebase for VR.** If VR happens, the web POC becomes a thin viewer fed by
  exported files with zero analysis logic. See
  [ADR-009](DECISIONS/ADR-009-web-poc-disposition.md).
- **Merging the ear application into this one.** See
  [ADR-002](DECISIONS/ADR-002-brain-ear-split.md). Unbudgeted work, zero evaluation value.
- **Re-litigating the stack.** Closed in [ADR-003](DECISIONS/ADR-003-application-shell.md).
  Reopening requires new measured evidence, not a preference.
- **Shipping an MMSE implementation.** Licence-blocked. See
  [`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md) and
  [ADR-005](DECISIONS/ADR-005-cognitive-instrument.md).

<a id="review-use"></a>

## How to use this in a review

For any proposed feature, answer in order:

1. Which user story in [`07-SRS.md`](07-SRS.md) does it serve? If none, it is out.
2. Which number does it produce that lands in a results table? If none, it is a demo feature
   and gets built last, cheaply.
3. Does it appear in this document? If yes, it needs a change record, not a decision in a
   meeting.
4. What does it displace? Schedule is fixed. Nothing is added; things are traded.

<a id="change"></a>

## Change procedure

A non-goal can be changed. It cannot be changed silently.

1. Open an ADR proposing the change, using [ADR-000](DECISIONS/ADR-000-template.md).
2. State what is being traded out of the schedule to pay for it.
3. State the new number it will produce.
4. Two reviewers. Weeks 13 to 22 are sacred: no scope change is accepted during R2.

---

**Related:** [`01-VISION_AND_SCOPE.md`](01-VISION_AND_SCOPE.md) ·
[`21-RISK_REGISTER.md`](21-RISK_REGISTER.md) ·
[research plan non-goals](research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#non-goals)
