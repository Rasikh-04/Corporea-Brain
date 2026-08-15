# 12 — Security, privacy and compliance

<a id="threat-model"></a>

## Threat model

Be honest about what this is. A single-laptop, offline, single-user application holding
de-identified or locally-identified patient records, built by students, not certified, not
audited. The realistic threats, in order of likelihood:

| # | Threat | Likelihood | Impact | Addressed by |
|---|---|---|---|---|
| T1 | Laptop lost or stolen with records on it | High | Severe | Encryption at rest, no plaintext store |
| T2 | Patient data accidentally committed to a public repository | High | Severe | `.gitignore` discipline, pre-commit scan, PR review item |
| T3 | Identifiers survive a de-identification that was assumed to work | Medium | Severe | De-identification verified by test, not by inspection |
| T4 | PHI burned into pixel data, unaffected by header scrubbing | Medium | Severe | Secondary-capture detection, explicit exclusion |
| T5 | Un-defaced T1 volume rendered in 3D, which is a photograph | Medium | Severe | Defacing required, checked |
| T6 | Data leaves the machine through an unexpected outbound call | Low | Severe | No-outbound default, packet-level offline test |
| T7 | A malicious or careless third-party extension or UI bundle | Low | High | Pinned extensions, bundles are data and cannot execute |
| T8 | Record store corruption losing a patient's history | Medium | High | Fail loud at open, backup before migration, checksums |

**Out of scope, stated plainly:** multi-user access control, network attack surface, tamper
resistance, formal security certification. There is no server and no network service. Saying
so is better than implying a security posture we do not have.

<a id="classification"></a>

## Data classification

| Class | Examples | Handling |
|---|---|---|
| **Identified PHI** | Name, parent names, address, facility, phone, date of birth, local MRN, un-defaced T1 | Encrypted at rest. Access logged including reads. Never exported without an explicit identified-export action. Never in git. |
| **Quasi-identifiers** | Age band plus city plus facility plus a rare condition | Treated as identified in combination. This combination re-identifies a person in a small cohort. |
| **De-identified clinical** | Measurements, scores, masks, attribution results, defaced volumes | Local. Not in git, because dataset agreements and hospital terms restrict redistribution regardless of de-identification. |
| **Derived non-clinical** | Timings, metrics, results tables, QC summaries | Freely shareable. This is what goes in the thesis. |
| **Public reference** | Atlases, templates, model weights, tract atlas | Redistributable subject to their own licences. See [`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md). |

<a id="deid"></a>

## De-identification as a projection, not a deletion

Both the identified and the de-identified copy are produced by **one script, from one source,
through two projections**. This is the pattern the ear work established and it is correct: two
independently-maintained copies drift, and the drift is invisible until it matters.

The public projection must:

- generalise date of birth to a ten-year age band and drop the raw date
- drop name, parent names, address, city, facility, telephone and mobile
- **drop or human-review free-text complaint and comment fields**, because prose carries
  identifying detail that no field-level rule catches
- assign an opaque case identifier not derived from any real identifier, not from a row id,
  and not from a hash of a name
- **retain all clinical measurements** — de-identification removes identity, not data

The free-text review is a human step, marked `TODO(deid-review)` in the pipeline. **No
de-identified export ships until it is complete.** This is enforced by the export path, not by
a note in a document.

<a id="defacing"></a>

## Defacing

Required for T1 MRI. Not optional, not a stretch goal.

A volume render of an un-defaced head is a recognisable photograph of the patient, and this
application renders volumes in 3D by design. Header de-identification does nothing about it.

Checked two ways: an automated face-detection check on a render of the defaced volume, and a
visual check in the per-case QC report. A volume that fails the check cannot be rendered in 3D
without an explicit logged override.

Watch the failure mode in the other direction: defacing that removes anatomy the analysis
needs, particularly for lesions near the orbitofrontal surface. Record when defacing altered
voxels inside the brain mask.

<a id="encryption"></a>

## Encryption at rest

- The record store and the per-case directory are encrypted at rest.
- Encryption is on by default. There is no "encrypt later" toggle, because there never is a
  later.
- A store that cannot be decrypted fails loudly at open with a specific message. It never opens
  partially and never silently creates a new empty store, which would look to a user like data
  loss and would be data loss.

<a id="keys"></a>

## Key handling

The honest position for an FYP, written down rather than hand-waved:

- The key is derived from a passphrase the operator sets at first run, using a memory-hard
  derivation function with parameters recorded in the configuration.
- **The key is never written to disk in plaintext, never logged, and never in an environment
  variable committed anywhere.**
- There is **no key escrow and no recovery**. A lost passphrase means lost data. This is stated
  in the application at first run, in plain language, and it is stated in the report as a
  limitation. Building a recovery mechanism badly is worse than not building one.
- Rotation: supported by re-encrypting the store, tested on a fixture, backup written first.

<a id="access"></a>

## Access control and the single identity seam

There is one user. There is no login for the application itself; the passphrase gates the
store, which is the thing that matters.

Where identified fields are involved, **all code that knows identities exist lives behind one
seam** — a single resolver that takes a case identifier and returns identity fields for that one
case. It never returns a list and it never runs at build time. This is the EarTwin identity
route pattern and it holds here for the same reason: if the identity set later outgrows local
storage, one file changes and nothing else in the application does.

<a id="audit"></a>

## Audit log requirements

Append-only. Tamper-evident by chaining checksums, which is proportionate for this context and
cheap.

Logged: every state-changing operation, every read of an identified field, every override of a
QC failure, every de-identified export, every classification correction, every decryption
attempt including failures.

Not logged: the data itself. An audit log containing PHI is a second copy of the PHI with
weaker protection. Log identifiers and actions, never values.

<a id="network"></a>

## Network posture

- **No outbound connection by default.** Not "no connection unless needed" — none.
- Anything that would need the network at runtime is either removed or explicitly gated behind
  a user action with a named destination.
- Model weights, atlases and templates are fetched by a separate downloader script, before
  deployment, never by the application at runtime.
- Telemetry, crash reporting and update checks: **none**. There is no acceptable version of
  "anonymous usage data" on a machine holding patient records in this context.
- Verified by the packet-level offline test in
  [`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md), not by reading the source.

<a id="logging"></a>

## Logging hygiene

The most common way student projects leak PHI is the log file.

Rules:

- **No patient identifier, name, date of birth or free-text clinical content in any log**, at
  any level, including debug.
- Log the opaque case identifier and the artifact identifier. Never the source path if it
  contains a name, which DICOM export directories frequently do.
- Exception traces are scrubbed before they are written, because a stack trace often carries a
  file path and a file path often carries a name.
- Logs rotate and are capped. An unbounded log on a clinic laptop is its own problem.
- A test asserts that a full pipeline run on a PHI-seeded synthetic study produces a log
  containing none of the seeded values. This is cheap and it is the check that actually works.

<a id="incident"></a>

## Incident procedure

Small project, so keep it small and actually followable.

1. **Stop.** Do not push, do not delete, do not rewrite history yet.
2. Tell the lead and the governance owner the same day.
3. Establish what left the machine and where it went.
4. If it reached a public repository: remove the content, rewrite history, rotate anything
   exposed, and **assume it was retrieved**, because it was.
5. Write the incident up in `docs/DECISIONS/` as a record. It is not a punishment; it is the
   only way the next person does not repeat it.
6. Tell the institution and the data provider if any real patient data was involved. This is
   not optional and delaying it makes it worse.

<a id="out-of-scope"></a>

## Out of scope for this project, stated

Recorded so that a reviewer sees the boundary was drawn deliberately.

- Formal security certification or penetration testing.
- Multi-user roles, permissions, or federated identity.
- Network hardening, because there is no network service.
- Key escrow, recovery and enterprise key management.
- Tamper-resistant audit storage beyond checksum chaining.
- Long-term archival, retention scheduling and legal hold.

Each is a genuine requirement for a real clinical deployment and each is named in the
limitations chapter as future work rather than quietly omitted.

---

**Related:** [`05-DATA_MODEL.md`](05-DATA_MODEL.md) ·
[`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) ·
[`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md) ·
[`16-TESTING_STRATEGY.md`](16-TESTING_STRATEGY.md)
