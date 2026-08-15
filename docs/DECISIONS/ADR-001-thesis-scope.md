# ADR-001 — Thesis scope and the surviving claim

**Status:** Accepted
**Date:** 2026-08-15
**Owner:** Lead
**Blocks:** Everything

## Context

The original concept document described four distinct products stacked on each other: an
interactive whole-body anatomical atlas, a structured disorder knowledge base, a
patient-specific imaging and record system, and a predictive simulative digital twin.

A landscape audit established that product 1 is a solved commodity, product 2 is a content
problem that is also solved, and product 4 is a decade-scale research programme currently
running a 356-patient randomised trial. Only product 3 has an unclaimed gap in it.

Two further facts from the clinical interview constrain the framing. Clinical diagnostic
accuracy was reported near 99 percent, with imaging contributing roughly 30 percent of
diagnostic weight — which removes the headroom for a diagnostic aid. And the interviewee
emphasised structured history, family history and genogram, handedness, and eloquent-area
awareness, none of which any existing tool assembles.

## Options considered

| Option | Feasible | Novel | Evaluable | Data-safe | Wanted | Score |
|---|---|---|---|---|---|---|
| T-A Longitudinal neuro case workstation | 4 | 4 | 4 | 4 | 5 | 25 |
| **T-B Lesion to region to deficit mapper** | 4 | 4 | 5 | 5 | 4 | **27** |
| T-C Teaching twin | 5 | 2 | 4 | 5 | 3 | 24 |
| T-D Mechanistic simulation twin | 1 | 1 | 2 | 3 | 2 | 11 |

## Decision

**Build T-B as the technical core, inside the T-A product frame, with T-C as the demonstration
layer. Cite T-D as future work.**

Concretely: an open, offline-capable neuro case workstation that ingests a patient's DICOM
study, produces quantified and anatomically localised lesion characterisation for ischemic
stroke and glioma, attributes involvement to atlas regions and white-matter tracts with
explicit uncertainty, presents literature-referenced clinical correlates as hypotheses rather
than conclusions, and maintains all of it alongside a structured longitudinal neuro record —
running on a single laptop with no PACS dependency.

## Consequences

**Accepted costs.** No whole-body coverage, no diagnosis claim, no surgical planning claim, no
mechanistic simulation. Six non-goals recorded in [`../02-NON_GOALS.md`](../02-NON_GOALS.md).

**What this closes.** The scope debate. Reopening requires an ADR naming what is traded out of
the schedule to pay for the addition.

**What this enables.** An evaluation that completes on public data alone, which de-risks the
single largest procurement dependency. It also reuses the existing case data and atlas assets.

## Evidence

The landscape audit across four tiers — commercial systems, research digital twins, the
open-source imaging stack, and anatomy education tools — established what each of the four
candidate products would be competing against, and the four surviving gaps. The interview
notes supply the clinical grounding.

## Revisit trigger

The instructor formally redirects the deliverable, or the clinical relationship is lost and no
substitute is found, either of which changes what is defensible.
