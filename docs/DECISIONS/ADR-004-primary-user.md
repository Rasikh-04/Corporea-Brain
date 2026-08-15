# ADR-004 — Primary and secondary user

**Status:** Open
**Date raised:** 2026-08-15
**Owner:** Lead
**Deadline:** End of Phase 0
**Blocks:** User story priority, screen priority in [`../08-UI_UX_SPEC.md`](../08-UI_UX_SPEC.md), the E5 participant pool

## Context

Four candidate users emerge from the clinical interview, each with a different moment, a
different time budget and a different need. Without picking one primary, every requirement is
unfalsifiable and every feature is arguable forever.

| User | Moment | Time | Needs |
|---|---|---|---|
| Neurologist | Outpatient consult | 5 to 10 min | Fast summary; what changed; structured history |
| Neuroradiologist | Reporting a study | 10 to 30 min | Quantification and comparison to prior. **Not another viewer** |
| Neurosurgeon | Pre-operative review | 30 to 90 min | Lesion relative to eloquent regions and tracts |
| Trainee | Study time | Unbounded | Explanation and clinical-anatomical correlation |

## Options considered

| Primary | Secondary | Pros | Cons |
|---|---|---|---|
| **Neurologist** | Trainee | Matches the available clinical contact directly. Longitudinal record is their need. Hardest time constraint, which forces good design | Five minutes is brutal, and it constrains every screen |
| Neuroradiologist | Neurologist | Quantification is squarely their need | Competes with entrenched reporting workstations. "Not another viewer" is a real objection |
| Neurosurgeon | Neurologist | Eloquent-area concern was volunteered | Pushes toward R3, which is not the thesis artifact. Closest to the regulated commercial category |

## Recommendation, pending confirmation

**Neurologist primary, trainee secondary.** The available clinical relationship is a
neurologist, the longitudinal record — the strongest differentiator — is their need, and the
trainee group carries lower regulatory risk and is a realistic E5 participant pool.

## What is needed to close this

One conversation with the clinician confirming who would actually open this application, and
at which point in the patient journey. Fifteen minutes.

## Consequences of leaving it open

Screen priority in S5 to S7 is provisional. The E5 participant pool is unplanned. User stories
US-01 to US-12 are written against the recommendation and will need revision if it changes.
