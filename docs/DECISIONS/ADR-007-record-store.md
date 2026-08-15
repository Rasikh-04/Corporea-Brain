# ADR-007 — Record store technology

**Status:** Open
**Date raised:** 2026-08-15
**Owner:** Backend
**Deadline:** Before R2 implementation
**Blocks:** `ClinicalRecord`, `Timeline`, provenance persistence, the audit log

## Context

The longitudinal neuro record is the project's strongest differentiator and it lives at the
body layer, not inside an organ module. It must be queryable across time, versioned,
encrypted at rest, auditable, and entirely local with no server.

The web proof of concept used static JSON, which was the right answer for a POC with no
runtime backend and is the wrong answer here: a longitudinal record must be queried, migrated
and encrypted, and JSON files provide none of those.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **SQLite, with an encryption extension** | Ubiquitous, single file, transactional, real queries, well-understood migrations, trivially backed up, available inside Slicer's Python | Schema migrations must be written and tested. Encryption needs a vetted extension |
| Embedded document store | Flexible schema, less migration friction early | **Flexible schema is a liability for a clinical record.** Weaker query support for the timeline. Fewer encryption options |
| Files plus an index | Simplest to reason about; artifacts are already files | Reimplements a database badly. No transactions, so a partial write is a corrupted record |
| Slicer's MRML scene as the store | Already present | **Wrong tool.** MRML is a scene model, not a database. No queries, no migrations, no encryption, and it would violate the architectural seam that says a node holds a reference, not the truth |

## Recommendation, pending confirmation

**SQLite with a vetted encryption extension.** The record is relational — patient, study,
series, artifact, observation, score, relative — the timeline is a query, the audit log is an
append-only table, and single-file backup before migration is a one-line operation.

The relational shape was already sketched in the web POC and maps cleanly onto
[`../05-DATA_MODEL.md`](../05-DATA_MODEL.md). Moving to it is a load step, not a redesign.

## What is needed to close this

1. Verify an encryption option that is available on both Linux and Windows, buildable inside
   the Slicer environment, and licence-compatible with an Apache-2.0 release.
2. Confirm the imaging artifacts stay on disk with the store holding references and checksums.
   The database must not become a blob store.
3. Write and test one migration against a golden fixture store, including the mandatory
   verified backup step, before committing to the approach.

## Consequences of leaving it open

`ClinicalRecord` and `Timeline` cannot be implemented, and they are R2 work. The audit log and
encryption-at-rest requirements in
[`../12-SECURITY_PRIVACY_COMPLIANCE.md`](../12-SECURITY_PRIVACY_COMPLIANCE.md) have no
mechanism behind them.
