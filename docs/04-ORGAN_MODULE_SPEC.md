# 04 — Organ module specification

<a id="why"></a>

## Why a contract exists

The claim is not "we modelled the human body." The claim is **"we built an organ-agnostic
platform and implemented the brain to depth in it."** That is defensible, demonstrable and
true. This contract is what makes it true rather than rhetorical.

Three consequences follow from having it, all of them wanted:

1. **The body claim becomes structural.** Ship brain (deep), ear (shallow) and three or four
   stubs. The UI honestly displays implementation level. Nobody can allege over-claiming
   because the application itself says "stub."
2. **`known_gaps` does real work.** The Z-Anatomy finding — dural sinuses present but no
   cerebral veins, cranial nerves clipped at the skull base — becomes a machine-readable,
   displayed limitation instead of a hidden defect. Turning a known weakness into a declared
   feature is exactly the move that earns credit.
3. **The ear workstream stops being a fork.** It becomes a second instance of one contract,
   which is evidence *for* the architecture rather than a competitor for time.

<a id="manifest"></a>

## Manifest schema

One file per organ: `organs/<organ>/manifest.yaml`.

```yaml
organ: brain                       # required, lowercase slug, unique
display_name: "Brain"              # required
implementation_level: deep         # required: deep | shallow | stub
schema_version: 1                  # required

geometry:
  entry_mesh: assets/brain/shell.glb          # required for all levels
  layers:                                      # optional, deep and shallow only
    - id: cortex
      mesh: assets/brain/cortex.glb
    - id: deep-grey
      mesh: assets/brain/deep-grey.glb
    - id: ventricles
      mesh: assets/brain/ventricles.glb
    - id: white-matter-tracts
      mesh: assets/brain/tracts.glb
    - id: vasculature
      mesh: assets/brain/vasculature.glb

parcellations:                     # required for deep, optional shallow, absent for stub
  - desikan-killiany
  - harvard-oxford
  - jhu-wm

supported_modalities: [MR-T1, MR-T1CE, MR-T2, MR-FLAIR, MR-DWI, CT]

disorders:                         # required for deep and shallow
  - ischemic_stroke
  - glioma
  - intracerebral_haemorrhage

capabilities:                      # required; drives which UI affordances appear
  - segmentation
  - attribution
  - deficits
  - navigation
  - longitudinal

provenance:                        # required for every level, including stub
  source: "Z-Anatomy 2.0 derived"
  licence: "CC BY-SA 4.0"
  licence_url: "https://creativecommons.org/licenses/by-sa/4.0/"
  attribution_required: true
  generated_by: "pipeline/atlas/export_brain.py@v0.3.1"
  generated_on: "2026-08-15"
  known_gaps:
    - id: no-cerebral-veins
      statement: "Dural sinuses are present. Cerebral veins are absent."
      affects_layers: [vasculature]
      consequence: "No vascular claim of any kind may be made from this model."
    - id: cranial-nerves-clipped
      statement: "Cranial nerves are clipped at the skull base."
      affects_layers: [deep-grey]
      consequence: "Cisternal and extracranial segments are not represented."
```

<a id="fields"></a>

## Field reference

| Field | Type | Required | Notes |
|---|---|---|---|
| `organ` | slug | always | Unique across the registry. Lowercase, hyphenated. |
| `display_name` | string | always | Shown in the picker. |
| `implementation_level` | enum | always | `deep`, `shallow`, `stub`. Drives badges and capability gating. |
| `schema_version` | int | always | Bump on any breaking change to this document. |
| `geometry.entry_mesh` | path | always | The mesh shown when the organ is picked from the body shell. |
| `geometry.layers[]` | list | deep, shallow | Each layer is independently toggleable in the UI. |
| `parcellations[]` | list of ids | deep | Ordered; the first is the default. Ids resolve against ADR-006. |
| `supported_modalities[]` | list | deep, shallow | Used to warn when a study contains nothing usable. |
| `disorders[]` | list of ids | deep, shallow | Resolves against the disorder catalog. |
| `capabilities[]` | list | always | Missing capability means the affordance is not rendered. Never rendered-and-disabled without a reason string. |
| `provenance.source` | string | always | Where the geometry came from. |
| `provenance.licence` | SPDX or name | always | Audited before release. See [`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md). |
| `provenance.generated_by` | string | always | Script and version that produced the assets. |
| `provenance.known_gaps[]` | list | always | May be empty, must be present. See below. |

<a id="levels"></a>

## Implementation levels

| Level | Must provide | May provide | Must not claim |
|---|---|---|---|
| **stub** | `entry_mesh`, name, provenance, empty capability list | nothing else | Anything beyond identification |
| **shallow** | Entry mesh, labelled structures, at least one disorder mapping, provenance | Layers, one parcellation | Patient-specific quantification |
| **deep** | Everything shallow, plus segmentation, attribution, deficits, longitudinal | Navigation | Anything above the fidelity tier it was built at |

The UI **must** display the level as a badge on the organ picker and in the organ's own
header. A stub organ renders its mesh, its name, and the literal text "Not implemented in
this release." It never renders an empty analysis panel.

<a id="known-gaps"></a>

## The `known_gaps` field and why it is load-bearing

This is the most important field in the manifest and the one most likely to be treated as
optional. It is not.

Rules:

1. **It is present on every manifest, including stubs.** An empty list is a claim that the
   geometry is complete, and that claim requires evidence.
2. **Gaps are discovered from the geometry, never from the source's description files.** The
   ear work established this the hard way: Z-Anatomy names structures that exist only as
   label leader lines, not as surfaces. Inventory what is actually there.
3. **Every gap names the layers it affects and the consequence.** "No cerebral veins" is a
   note. "No vascular claim of any kind may be made from this model" is a constraint the UI
   and the report both honour.
4. **The UI surfaces the gap on the affected layer**, at the point of use, not in an About
   dialog. Toggling the vasculature layer shows the note.
5. **Where a disorder's primary site has no geometry, the highlight is substituted onto the
   nearest exported structure and the substitution is recorded in the case file.** It is never
   silently dropped and never silently approximated.

<a id="registration"></a>

## Registration and discovery

At startup the `OrganRegistry`:

1. Scans `organs/*/manifest.yaml`.
2. Validates each against the schema. A manifest that fails validation is **reported in the
   UI and the log with the specific failing field**, and the organ is excluded. It is never
   silently skipped.
3. Verifies every referenced asset exists and its checksum matches the manifest. A missing
   asset is a hard error at load, not a blank mesh at render.
4. Builds the picker list, sorted by implementation level then name.

<a id="ui-obligations"></a>

## UI obligations of a module

Every organ module, at any level, must:

- Render its implementation-level badge in its own header.
- Expose every `known_gaps` entry at the point of use.
- Show the current parcellation and coordinate space in a persistent, non-modal location.
  A user must never have to guess which atlas produced a label.
- Render a `NEEDS_SOURCE` description as a visible pending placeholder, never as blank and
  never with substituted text.
- Honour the active UI bundle. See [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md).

<a id="validation"></a>

## Validation

`scripts/validate_organs.py` runs in CI on every PR. It checks:

- schema conformance for every manifest
- asset existence and checksum
- that every `disorders[]` id resolves in the disorder catalog
- that every `parcellations[]` id resolves against the space configured in ADR-006
- that `capabilities[]` is consistent with `implementation_level`
- that `provenance.licence` is present and is in the approved list
- that `known_gaps` is present

CI failure blocks merge. This is the same posture the POC repositories used for their data
contracts, and it worked.

<a id="example-brain"></a>

## Worked example: brain (deep)

The manifest above. Capabilities all present. Three parcellations, default first. Two known
gaps, both surfaced on the vasculature and deep-grey layers.

<a id="example-ear"></a>

## Worked example: ear (shallow)

```yaml
organ: ear
display_name: "Ear"
implementation_level: shallow
schema_version: 1
geometry:
  entry_mesh: assets/ear/head-shell.glb
  layers:
    - {id: temporal-bone, mesh: assets/ear/temporal-bone.glb}
    - {id: outer,  mesh: assets/ear/ear-outer.glb}
    - {id: middle, mesh: assets/ear/ear-middle.glb}
    - {id: inner,  mesh: assets/ear/ear-inner.glb}
supported_modalities: []
disorders: [otitis_media_effusion, cerumen_impaction, sensorineural_loss]
capabilities: []
provenance:
  source: "Z-Anatomy 2.0 derived"
  licence: "CC BY-SA 4.0"
  generated_by: "pipeline/atlas/export_ear.py@v0.1.0"
  known_gaps:
    - id: no-external-acoustic-meatus
      statement: "The external acoustic meatus is a lumen and has no surface in the source."
      affects_layers: [outer]
      consequence: "Canal pathology is indicated on the temporal bone, not on a canal."
    - id: stapes-single-body
      statement: "Base and limbs of the stapes exist only as label anchors; the stapes ships as one mesh."
      affects_layers: [middle]
      consequence: "Sub-stapedial localisation is not available."
```

Note `capabilities: []`. The ear carries disorder mappings but no patient-specific
quantification, which is exactly the intent of shallow. This is what keeps the ear from
quietly becoming a second product.

<a id="example-stub"></a>

## Worked example: stub

```yaml
organ: heart
display_name: "Heart"
implementation_level: stub
schema_version: 1
geometry: {entry_mesh: assets/heart/shell.glb}
supported_modalities: []
disorders: []
capabilities: []
provenance:
  source: "BodyParts3D"
  licence: "CC BY-SA 2.1 JP"
  generated_by: "pipeline/atlas/export_stub.py@v0.1.0"
  known_gaps:
    - id: shell-only
      statement: "External surface only. No chambers, valves or vessels."
      affects_layers: []
      consequence: "Identification only. No anatomical claim below the surface."
```

---

**Related:** [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md) ·
[`08-UI_UX_SPEC.md`](08-UI_UX_SPEC.md) ·
[`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md) ·
[build plan organ contract](research/FYP_Brain_Digital_Twin_Build_Plan.md#architecture)
