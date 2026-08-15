# ADR-002 — Brain and ear are separate deliverables

**Status:** Accepted
**Date:** 2026-08-15
**Owner:** Lead
**Blocks:** Team allocation, organ module scope

## Context

Three workstreams existed simultaneously against one small team over a summer break with
failing coordination: an approved brain proof of concept, an instructor-assigned ear rebuild,
and an intention to merge both into one desktop application eventually.

The ear work has since produced genuinely good design — a two-tier identity model, a derived
disorder rule engine with declared input requirements, and an atlas coverage document
generated from geometry rather than from description files. It is not wasted work. But it is a
second product competing for the same weeks.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Merge both into one application now | Satisfies the instruction literally; one codebase | Unbudgeted integration work with **zero evaluation value**; puts the ear on the critical path for the thesis artifact |
| **Ear as a separate deliverable, shared contract only** | Satisfies the instruction; protects R2; ear becomes evidence *for* the architecture | Two repositories to maintain |
| Drop the ear | Maximum focus | Ignores an explicit instruction |

## Decision

**The ear is delivered as a separate, self-contained deliverable that satisfies the
instruction and is explicitly out of the FYP's evaluated scope.** It shares the organ module
contract and design patterns, not code and not a release.

Within this application, an ear organ module may exist at **shallow** implementation level:
labelled structures and disorder mappings, `capabilities: []`, no patient-specific
quantification. Enforced by the organ contract, not by intention.

## Consequences

**Accepted costs.** The instruction is satisfied in a different shape than "one merged app."
This needs to be communicated in writing, with a recommendation, rather than as an open
question.

**What this closes.** Merging the two applications during the FYP. Reopening requires an ADR
naming what is traded out.

**What this enables.** R2 keeps its weeks. And the ear, as a second instance of one contract at
a different depth, becomes evidence that the architecture is genuinely organ-agnostic — which
is a stronger demonstration than a merged monolith would be.

## Evidence

The ear workstream consuming brain capacity is a High likelihood, High impact risk in both the
research plan and [`../21-RISK_REGISTER.md`](../21-RISK_REGISTER.md). The shallow-tier
mechanism in [`../04-ORGAN_MODULE_SPEC.md`](../04-ORGAN_MODULE_SPEC.md) is what enforces it.

## Revisit trigger

R2 reaches Validated fidelity for two disorders ahead of schedule and there is spare capacity
before the freeze.
