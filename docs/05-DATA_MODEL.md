# 05 — Data model

The record store, timeline and provenance live at the **body layer**, not inside an organ
module. This is the differentiator the landscape audit identified, and burying it in an
organ would destroy both its reusability and the architectural claim.

Storage technology is [ADR-007](DECISIONS/ADR-007-record-store.md), still open. This document
specifies the model, not the engine. Everything below is engine-neutral.

<a id="principles"></a>

## Principles

1. **Every derived value carries provenance.** Source, tool, version, parameters, timestamp.
   Without it Chapter 4 is unwritable and nothing is reproducible.
2. **Every derived value carries uncertainty.** A number with no stated uncertainty is a
   claim the system is not entitled to make.
3. **Controlled vocabularies where they exist.** Rolling our own free-text fields for
   diagnoses and observations will be flagged in review.
4. **Identity is a projection, not a deletion.** De-identified and identified copies are two
   projections of one source, produced by one script. Removal of a name is not sufficient
   de-identification and the model reflects that.
5. **Nothing is destroyed.** Corrections are new versions with a supersedes link. The audit
   log is append-only.
6. **Units are explicit on every quantity.** Millimetres, millilitres, ISO-8601 dates. No
   bare numbers.

<a id="overview"></a>

## Entity overview

```
Patient ──┬── Study ──── Series ──── DerivedArtifact
          │                              │
          │                              ├── SegmentationResult
          │                              ├── ParcellationResult
          │                              └── AttributionResult ── DeficitHypothesis
          │
          ├── Observation   (examination findings, symptoms, events)
          ├── Score         (NIHSS, mRS, GCS, KPS, cognitive instrument)
          ├── Medication
          ├── Comorbidity
          └── Relative ──── (genogram edges)

TimelineEntry is a view over Study, Observation, Score, Medication and
DerivedArtifact, not a table of its own.
```

<a id="patient"></a>

## Patient

| Field | Type | Notes |
|---|---|---|
| `patient_id` | opaque id | Assigned locally. Never derived from a name, MRN, or any real identifier. Format `pt-<counter>`. |
| `sex` | enum | `female`, `male`, `other`, `unknown`. Administrative sex; record biological sex separately if the clinician requires it. |
| `date_of_birth` | ISO-8601 date | Identified projection only. |
| `age_band` | string | De-identified projection. Ten-year bands, e.g. `40-49`. |
| `handedness` | enum | `right`, `left`, `ambidextrous`, `unknown`. **Mandatory.** The clinician called this out specifically: handedness determines language lateralisation and therefore which regions are eloquent. |
| `occupation` | coded + free text | |
| `marital_status` | enum | |
| `education_years` | int | Needed to interpret cognitive scores. |
| `obstetric_history` | structured | Where applicable. |
| `addiction_history` | structured | Substance, duration, current status. |
| `allergies[]` | coded | |
| `review_status` | enum | `pending`, `reviewed`. Mirrors the POC convention that worked. |

**Handedness is a required field at case creation.** The application must not allow a case to
reach attribution with handedness unknown without displaying an explicit warning that
eloquent-region interpretation is unreliable.

<a id="study-series"></a>

## Study and Series

| Entity | Key fields |
|---|---|
| `Study` | `study_id`, `patient_id`, `study_date` (ISO-8601), `modality_set[]`, `source_media` (`usb`, `cd`, `folder`), `ingest_timestamp`, `deidentified` (bool), `qc_report_ref` |
| `Series` | `series_id`, `study_id`, `declared_description` (raw `SeriesDescription`), `classified_sequence` (enum), `classification_confidence` (0..1), `classification_method` (`rule`, `learned`, `manual`), `corrected_by_user` (bool), `voxel_spacing_mm[3]`, `dimensions[3]`, `orientation_code` (e.g. `RAS`), `nifti_ref` |

`classified_sequence` is one of `T1`, `T1CE`, `T2`, `FLAIR`, `DWI`, `ADC`, `SWI`, `CT`,
`UNKNOWN`.

**Three rules on classification, all of them safety rules:**

- The guess is always displayed. It is never applied silently.
- The user can always correct it, and the correction sets `corrected_by_user`.
- Every assignment is logged, with the method and confidence, so classifier accuracy can be
  measured after the fact from real use. That measurement is the number R0 emits.

<a id="derived"></a>

## DerivedArtifact and provenance

Every computed thing is a `DerivedArtifact`. No exceptions, including intermediate volumes.

| Field | Type | Notes |
|---|---|---|
| `artifact_id` | id | |
| `kind` | enum | `preprocessed_volume`, `mask`, `parcellation`, `mesh`, `measurement`, `report` |
| `source_refs[]` | ids | Every input, by id. Enables the full lineage graph. |
| `tool` | string | e.g. `nnUNet`, `FastSurfer`, `ANTs`, `dcm2niix` |
| `tool_version` | string | Exact. Not "latest". |
| `parameters` | map | The full invocation parameters, serialised. |
| `coordinate_space` | string | Resolved per ADR-006. e.g. `subject-native-RAS`, `MNI152NLin2009cAsym`. |
| `created_at` | ISO-8601 datetime | |
| `checksum` | sha256 | Of the artifact bytes. |
| `supersedes` | id or null | For corrections and re-runs. |
| `file_ref` | path | Relative to the case root. Never absolute. |

**Reproducibility test:** given only the `DerivedArtifact` rows, a person on a different
machine must be able to reconstruct the command that produced each one. If they cannot, the
provenance is incomplete. This is a CI check on the golden case.

<a id="results"></a>

## Segmentation and Attribution results

`SegmentationResult`

| Field | Notes |
|---|---|
| `mask_ref` | The `DerivedArtifact` id |
| `disorder_id` | `ischemic_stroke`, `glioma`, `intracerebral_haemorrhage` |
| `label_map` | e.g. `{1: "necrotic core", 2: "oedema", 4: "enhancing tumour"}` |
| `volume_ml` per label | With uncertainty band |
| `model` + `model_version` | |
| `confidence` | Model-reported where available; `null` where not, never fabricated |

`AttributionResult` — **the core contribution.** One row per involved region.

| Field | Notes |
|---|---|
| `region_id` | Resolves against the active parcellation |
| `role` | `primary`, `secondary` |
| `overlap_voxels` | int |
| `overlap_fraction_of_region` | 0..1 |
| `overlap_fraction_of_lesion` | 0..1 |
| `rank` | Ordinal within the case |
| `uncertainty_statement` | Required, non-empty. Names the specific sources of error: registration residual, partial volume, mass-effect distortion. |
| `provenance` | e.g. `computed: mask.nii.gz ∩ DK atlas in MNI152 space` |
| `substituted_from` | Set when the true site has no geometry and the highlight was moved. Null otherwise. |

**Never store a region attribution without an uncertainty statement.** A schema check
enforces it.

`DeficitHypothesis`

| Field | Notes |
|---|---|
| `source_region_id` or `source_tract_id` | |
| `expected_correlate` | Text, from the mapping table |
| `citation` | PMID, DOI or ISBN. Never empty. `NEEDS_SOURCE` blocks release. |
| `confidence_band` | `high`, `moderate`, `low` |
| `rank` | |

Hypotheses are **presented as hypotheses, never conclusions**, and are **ranked, never
filtered**. Honouring the clinician's guidance that missing is worse than over-flagging means
showing everything in order, not suppressing the tail.

<a id="observation"></a>

## Observation and Score

`Observation` — examination findings, symptoms, events.
Fields: `observation_id`, `patient_id`, `observed_at`, `code` (SNOMED CT where possible),
`display`, `value`, `unit`, `recorded_by`, `free_text`.

`Score` — standardised instruments.
Fields: `score_id`, `patient_id`, `instrument`, `instrument_version`, `administered_at`,
`raw_items` (map), `total`, `interpretation_band`, `administered_by`, `licence_ref`.

`licence_ref` is not decorative. It links to the entry in
[`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md) that authorises shipping that instrument.
An instrument with no licence entry cannot be created. **MMSE is blocked at this layer**, not
just by policy. See [ADR-005](DECISIONS/ADR-005-cognitive-instrument.md).

<a id="relative"></a>

## Relative and genogram

Fields: `relative_id`, `patient_id`, `relation` (coded), `sex`, `alive` (bool),
`age_or_age_at_death`, `conditions[]` (ICD-10), `consanguinity_flag`, `notes`.

Genogram edges are derived from `relation`, not stored separately. Rendering rules are in
[`08-UI_UX_SPEC.md`](08-UI_UX_SPEC.md).

The clinician emphasised family history, anamnesis and genogram. This is the part of the
record no neuronavigation system has and no EMR links to imaging quantification. It is a
pillar, not a footnote.

<a id="vocabularies"></a>

## Controlled vocabularies

| Domain | Vocabulary | Fallback |
|---|---|---|
| Diagnoses, comorbidities | ICD-10 | Free text with a `TODO(coding)` flag |
| Clinical findings | SNOMED CT where licensing permits | ICD-10, then free text |
| Observations, measurements | LOINC | Local code with a documented definition |
| Medications | ATC | Free text with generic name required |
| Anatomical regions | The active parcellation, per ADR-006 | None. Regions are never free text. |

Free text is allowed and is sometimes correct. Free text **masquerading as a code** is not.
Every fallback is flagged so the coding debt is visible.

<a id="identifiers"></a>

## Identifiers and de-identification

Two projections from one source, produced by one script, as in the EarTwin pattern:

| | Identified | De-identified |
|---|---|---|
| Name, parent names, address, city, facility, phone | present | **dropped** |
| Date of birth | present | generalised to a ten-year `age_band` |
| Free-text complaint and comments | present | **dropped or human-reviewed**, because prose carries identifying detail |
| Case identifier | local MRN | opaque counter, not derived from any real identifier |
| Clinical measurements | present | **present** — de-identification removes identity, not data |

Across a small cohort, date of birth plus city plus facility plus a named syndrome
re-identifies a person on its own. Name removal alone is not sufficient. The free-text review
is a human step, marked `TODO(deid-review)`, and no de-identified export ships until it is
done.

For T1 MRI, **defacing is required**, not optional. A 3D render of an un-defaced head is a
photograph. See [`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) Stage 2.

<a id="units"></a>

## Units and coordinate conventions in the record

- Lengths and distances: **millimetres**. Volumes: **millilitres**.
- Dates: **ISO-8601** `YYYY-MM-DD`. Timestamps: ISO-8601 with timezone offset.
- Every geometric value stores its `coordinate_space` alongside it. A coordinate with no
  space is meaningless and the schema rejects it.
- Voxel versus world coordinates are never mixed in one field. The field name says which.
- `orientation_code` is stored as a three-letter code (`RAS`, `LPS`) on every volume.

<a id="storage"></a>

## Storage and encryption at rest

- One local store per installation. No server, no sync, no cloud by default.
- Imaging artifacts live on disk under a per-case directory; the store holds references and
  checksums, not blobs.
- **Encryption at rest is required** for the record store and the case directory. Key
  handling in [`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md).
- A corrupted or truncated store must fail loudly at open. It must never silently open a
  partial record.

<a id="audit"></a>

## Audit log

Append-only. One row per state-changing operation.

Fields: `event_id`, `timestamp`, `actor`, `action`, `entity_type`, `entity_id`,
`before_checksum`, `after_checksum`, `app_version`.

Reads of identified fields are logged too, not just writes. That is the point of an audit log
in a clinical context.

<a id="export"></a>

## Export shapes

| Export | Format | Contains | Never contains |
|---|---|---|---|
| Structured report | PDF | Findings, attribution table, hypotheses with citations, uncertainty, disclaimer, provenance footer | Raw identifiers unless the identified projection was explicitly requested |
| Measurements | CSV | One row per measurement with units and provenance | |
| Full case | JSON | The complete record graph | |
| Scene for viewer | glTF + JSON | Geometry and labels | Any analysis logic. See [ADR-009](DECISIONS/ADR-009-web-poc-disposition.md) |

Every export carries the application version, the pipeline version and the disclaimer. An
export without provenance is not a valid export.

<a id="migration"></a>

## Migration policy

- `schema_version` on the store. Bump on any breaking change.
- Migrations are forward-only, scripted, and tested against a golden fixture store.
- A migration that cannot be tested does not ship.
- Never migrate in place without a backup written first, verified by checksum.

---

**Related:** [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md) ·
[`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) ·
[`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md) ·
[ADR-006](DECISIONS/ADR-006-coordinate-space-and-atlas.md) ·
[ADR-007](DECISIONS/ADR-007-record-store.md)
