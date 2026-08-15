# 13 — Legal and ethics

This document takes about a day to keep current and prevents a very bad viva moment. Every
register below is a living table; an empty cell is a risk.

<a id="components"></a>

## Component licence register

| Component | Licence | Obligation | Compatible with our Apache-2.0 release |
|---|---|---|---|
| 3D Slicer | BSD-style | Attribution | Yes. Permissive, supports unrestricted use with attribution. |
| SlicerCustomAppTemplate | Apache-2.0 | Attribution | Yes. Custom code we add may be licensed as we choose. |
| VTK, ITK, CTK | BSD-style | Attribution | Yes |
| Qt | LGPL or commercial | **Dynamic linking, relink capability, licence notice** | Yes if dynamically linked. Verify before shipping an installer. |
| SlicerIGT, SlicerOpenIGTLink, PLUS | BSD-style | Attribution | Yes |
| nnU-Net | Apache-2.0 | Attribution | Yes. **Pretrained weights carry separate terms — check each.** |
| FastSurfer | Check current | Often research-use restrictions on weights | **Verify before release** |
| SynthSeg | Check current | Often research-use restrictions | **Verify before release** |
| ANTs / Elastix | BSD-style / Apache | Attribution | Yes |
| dcm2niix | BSD-style | Attribution | Yes |

**Model weights are the trap.** A permissively-licensed framework frequently ships weights
under a research-use-only or non-commercial term. The framework licence is not the weight
licence. Every weight file gets its own row before it is used.

<a id="datasets"></a>

## Dataset agreement register

| Dataset | Access | Redistribution | Notes |
|---|---|---|---|
| ATLAS v2.0 | Registration | **Forbidden** | Stroke lesion masks |
| BraTS current edition | Challenge registration and terms | **Forbidden** | Glioma sub-regions |
| PhysioNet CT-ICH | Credentialing, low friction for this one | **Forbidden** | Haemorrhage on CT |
| OASIS-3 | Data use agreement | **Forbidden** | Longitudinal |
| ADNI | Application with a stated purpose | **Forbidden** | Only if needed |
| MNI152 templates | Open | Permitted with attribution | Reference space |
| JHU white matter atlas | Open | Check terms | Tract involvement |

**The operative rule, and it applies to every row: derived data is still derived from the
data.** A processed mask, a cropped volume, a mesh generated from a subject scan — all remain
covered. Ship a downloader script, never the data. Audit the repository before it is made
public.

<a id="assets"></a>

## Atlas and asset licences

| Asset | Source | Licence | Obligation |
|---|---|---|---|
| Brain and ear meshes | Z-Anatomy derived | CC BY-SA 4.0 | **Attribution and share-alike.** Share-alike affects the derived assets, not our application code. Keep the boundary explicit and documented. |
| Body-level shells | BodyParts3D or similar | CC BY-SA | Attribution and share-alike |
| Icons in the default UI bundle | Original or permissive | Recorded in the bundle manifest | Per bundle |

**Declared asset gaps, which are a licence-adjacent honesty matter:** the Z-Anatomy derived
brain model has dural sinuses but no cerebral veins, and cranial nerves are clipped at the
skull base. These are recorded in the organ manifest's `known_gaps`, surfaced in the UI, and
stated in the report. A known weakness declared is a strength; a known weakness hidden is a
finding against you.

<a id="instruments"></a>

## Clinical instrument licensing, and the MMSE problem

This is the specific landmine, because the interview notes say to integrate MMSE.

- **MMSE is copyrighted and commercially licensed.** Rights were exclusively licensed to a
  commercial publisher and licensed administrations are sold per use. It has been removed from
  textbooks and toolkits for this reason. **We cannot ship an MMSE implementation.** This is
  enforced in the data model: an instrument with no licence register entry cannot be
  instantiated.
- **MoCA** is also copyrighted, but the publisher permits use, reproduction and distribution by
  universities, health professionals, hospitals and clinics without further permission provided
  it is free to patients; administrator certification is required and is free for students,
  faculty and academic researchers. This is a workable academic path. **Read the current
  permission terms directly before building it in** — they have changed before.
- **Freely usable alternatives worth evaluating:** Mini-Cog, SLUMS and other open-access
  instruments.
- **NIHSS, mRS, KPS and GCS** are generally free to use. Verify each for the jurisdiction and
  confirm with the clinician which are actually used locally, since an instrument nobody uses
  locally is a feature nobody uses.

Decision pending in [ADR-005](DECISIONS/ADR-005-cognitive-instrument.md).

<a id="regulatory"></a>

## Regulatory framing

Software that influences a clinical decision is, in most jurisdictions, Software as a Medical
Device. We are not seeking clearance and we make no clearance claim.

The framing that keeps this honest:

- The system produces **findings and hypotheses**. A clinician decides. The distinction between
  decision support and diagnosis is legally meaningful and we sit clearly on one side of it.
- **No intra-operative use, no navigation, no registration to a physical patient.** R3 is
  planning on imaging. R5 is a measurement demonstrator against a phantom, with no human
  subjects and no accuracy claim transferable to patients.
- The disclaimer is shown **in the application**, at startup, before any data is loaded, and
  persistently in the context bar.

<a id="jurisdiction"></a>

## Jurisdiction, and why institutional governance binds instead

Pakistan has **no enacted comprehensive data protection law** as of mid-2026. PECA 2016, as
amended in January 2025, is a criminal statute. The Personal Data Protection Bill remains
pending; its drafts classify health and medical records as sensitive personal data.

**The absence of a law is not permission.** Three things bind instead, and examiners expect all
three to have been considered:

1. The **university ethics committee**, which is the formal approval route.
2. The **hospital's own governance**, which controls whether any data moves at all.
3. **International norms** — GDPR and HIPAA principles — which are what a competent examiner
   will measure the design against regardless of local law.

Design to the strictest of the three. It costs almost nothing at this scale and it is the only
defensible position.

<a id="ethics-route"></a>

## Ethics approval route

Long lead time. Start immediately, in parallel, with a named owner. Three to six months
minimum, and it can fail for reasons entirely outside the team's control.

1. Draft the ERC application **even if it is never submitted.** Drafting it forces every
   unresolved data question into the open, which is most of its value.
2. Submit the enquiry to the university ERC and the hospital contact in week 1, regardless of
   what else is happening.
3. Scope the application to **retrospective, de-identified data only**, which is the shortest
   path and the one most likely to be approved.
4. **Design the entire evaluation so it completes on public data alone.** Local data becomes a
   bonus chapter, never a dependency. This is already the design in
   [`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md); protect it.

<a id="consent"></a>

## Consent for retrospective de-identified data

Waiver of consent is commonly granted for retrospective de-identified research where obtaining
consent is impracticable and risk is minimal. That is a decision for the ERC, not for us. What
we supply:

- A documented, tested de-identification method.
- A defacing step for T1 MRI.
- A statement that no data leaves the institution's machine.
- A retention and destruction plan.
- A named accountable person.

<a id="disclaimer"></a>

## The in-application disclaimer

Shown at startup before any data loads, requiring acknowledgement, and repeated persistently in
the context bar. A UI bundle cannot remove it.

> **Not for clinical use.**
> BrainTwin Desktop is a research prototype developed as an undergraduate final year project.
> It has not been evaluated or approved by any regulatory authority and is not a medical device.
> It does not provide a diagnosis. All measurements are automated estimates carrying
> uncertainty, and all clinical correlates shown are literature-derived hypotheses, not
> findings. Every output requires independent verification by a qualified clinician. Do not use
> this software to make or support a decision about a patient's care.

Report exports carry the same text in the footer, alongside the provenance block.

<a id="attribution"></a>

## Attribution obligations

An `ATTRIBUTIONS.md` shipped with the application and reachable from an About dialog, listing
every component, dataset, atlas and instrument with its licence and required notice. Generated
from the registers above by a script, so it cannot fall out of date silently.

<a id="audit-checklist"></a>

## Pre-publication audit checklist

Run before the repository is made public, and again before submission. Every line is a hard
gate.

- [ ] No patient-derived data in the repository, including in git history
- [ ] No dataset files, processed or raw, including small samples
- [ ] No model weights whose licence forbids redistribution
- [ ] No credentials, keys, tokens or connection strings, including in history
- [ ] No real identifiers in fixtures, tests, screenshots or the demo recording
- [ ] Every component in the licence register, with its obligation satisfied
- [ ] `ATTRIBUTIONS.md` regenerated and matching the registers
- [ ] Share-alike boundary documented for CC BY-SA derived assets
- [ ] No licensed clinical instrument implemented in shippable code
- [ ] Disclaimer present in the application, in the README and in every export
- [ ] Downloader scripts present and working; no data path assumes local data exists
- [ ] Demo recording reviewed frame by frame for identifiers and un-defaced renders

---

**Related:** [`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md) ·
[`05-DATA_MODEL.md`](05-DATA_MODEL.md) ·
[ADR-005](DECISIONS/ADR-005-cognitive-instrument.md) ·
[research plan Hole 8](research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#hole-8)
