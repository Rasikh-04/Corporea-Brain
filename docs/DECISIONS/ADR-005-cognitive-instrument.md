# ADR-005 — Cognitive instrument selection

**Status:** Open
**Date raised:** 2026-08-15
**Owner:** Governance
**Deadline:** End of Phase 1
**Blocks:** Clinical record F5, the score timeline

## Context

The clinical interview says cognitive questionnaires can and should live in the application,
while physical scores such as GCS need in-person evaluation. It names MMSE.

**MMSE cannot ship.** It is copyrighted, its rights were exclusively licensed to a commercial
publisher, licensed administrations are sold per use, and it has been removed from textbooks
and toolkits as a result. Shipping an MMSE implementation in an open codebase is a licence
violation, and it is the kind that gets noticed.

## Options considered

| Instrument | Licensing | Clinical acceptance | Verdict |
|---|---|---|---|
| MMSE | **Commercially licensed, per-administration fee** | Very high | **Blocked** |
| MoCA | Copyrighted, but publisher permits use by universities, health professionals, hospitals and clinics without further permission provided it is free to patients. Administrator certification required, free for students, faculty and academic researchers | High | **Workable academic path. Read the current terms directly before building.** |
| Mini-Cog | Open access | Moderate, brief screening | Viable |
| SLUMS | Open access | Moderate | Viable |
| None; record externally administered scores only | No issue | n/a | Safe fallback |

NIHSS, mRS, KPS and GCS are generally free to use and are a separate question; verify each for
the jurisdiction.

## Recommendation, pending confirmation

**MoCA if the current permission terms are confirmed in writing and certification is obtained;
otherwise Mini-Cog.** Either way, the fallback of recording externally administered scores is
implemented first, because it is licence-free and is most of the value for the timeline.

## Enforcement, already decided

Regardless of which instrument is chosen, the constraint is enforced in the data model rather
than by policy: **a `Score` requires a `licence_ref` resolving to an entry in the licence
register, and an instrument with no entry cannot be instantiated.** A policy that lives only in
a document gets broken at two in the morning; a schema constraint does not. See
[`../05-DATA_MODEL.md`](../05-DATA_MODEL.md) and
[`../13-LEGAL_AND_ETHICS.md`](../13-LEGAL_AND_ETHICS.md).

## What is needed to close this

1. Read the publisher's current permission terms directly. They have changed before.
2. Ask the clinician which instrument is actually used locally. An instrument nobody uses
   locally is a feature nobody uses.
3. Obtain certification if MoCA is chosen.

## Consequences of leaving it open

F5.5 is unimplementable. The score timeline has no cognitive lane. E6 cannot be fully designed.
