# ADR-009 — Disposition of the web proof of concept

**Status:** Accepted
**Date:** 2026-08-15
**Owner:** Lead
**Blocks:** R4 planning, team allocation

## Context

The web proof of concept — Next.js, React Three Fiber, Niivue, with an offline Python
preprocessing side and a CI-validated JSON contract — works, was demonstrated, and is the
credibility anchor that got the project approved.

With the shell decided as a custom Slicer application ([ADR-003](ADR-003-application-shell.md)),
its future has to be settled explicitly, because the default outcome of leaving it unsettled is
two half-maintained codebases. That is a Medium likelihood, Medium impact risk in both the
build plan and [`../21-RISK_REGISTER.md`](../21-RISK_REGISTER.md), and it is the kind of risk
that materialises through drift rather than through a decision.

There is a genuine tension. The web stack is WebGL-based, which makes WebXR the cheapest
possible route to a standalone headset demonstration — a Quest running a real segmented case in
stereo, for a fraction of the effort of any native VR integration. That is a real asset and
throwing it away has a cost.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Maintain both as full applications | Keeps everything | **Two half-maintained codebases.** Guaranteed drift, doubled review burden, zero evaluated gain |
| Delete the web POC | Maximum focus | Discards the cheapest VR path and a working demo asset for no benefit |
| **Retire as a product; retain as an optional thin viewer** | Keeps the cheap standalone VR demo; costs about one engineer-week of export plumbing; no analysis logic to keep in sync | Still a second thing that exists, so the boundary must be enforced rather than intended |
| VR through SlicerVirtualReality instead | One codebase | Tethered PC VR rather than standalone. Heavier to demo. Still a viable alternative for R4 |

## Decision

**The web proof of concept is retired as a product. It is retained, optionally, as a thin
viewer fed by files the desktop application exports — with zero analysis logic.**

The boundary, enforced as an architectural seam:

- The viewer receives geometry, labels and precomputed overlays. Nothing else.
- **It computes nothing.** No segmentation, no attribution, no uncertainty, no hypotheses. If a
  number appears in the viewer, the desktop application computed it and exported it.
- It has no access to the record store, no patient data beyond what an export contains, and no
  identity resolution.
- It is not on the release path and it is not in the installer.

R4 chooses between this WebXR route and SlicerVirtualReality on the basis of which produces a
working demonstration inside its two-engineer-week kill criterion. Either is acceptable; R4 is
Demonstrator fidelity and is a showpiece, not a claim.

## Consequences

**Accepted costs.** A second repository continues to exist. The export format is one more thing
to version. About one engineer-week of plumbing if the route is taken.

**What this closes.** Any proposal to develop the web application further as a product, or to
place analysis logic in it. Both are rejected on sight.

**What this enables.** A standalone headset demo without a native VR integration, and honest
citation of the POC as prior work in the related-work chapter.

## Evidence

The build plan identifies this hybrid explicitly as the resolution to the native-versus-web
tension, at roughly one engineer-week of export plumbing, on the condition that the web side is
a thin renderer with no analysis logic. This ADR adopts that condition as an enforced
architectural seam rather than an intention.

## Revisit trigger

R4 is descoped entirely under its kill criterion, in which case the viewer is not built at all
and the POC is cited as prior work only.
