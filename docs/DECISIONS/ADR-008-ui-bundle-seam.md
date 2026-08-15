# ADR-008 — UI bundle seam, visual design deferred

**Status:** Accepted
**Date:** 2026-08-15
**Owner:** Lead
**Blocks:** Nothing. That is the point of it

## Context

Clinical software is function-dominant by convention and for good reasons: the user is thinking
about a patient, the interface must get out of the way, radiological reading is done on black,
and motion near a diagnostic image is a distraction with a clinical cost.

Meanwhile, this project's visual identity is genuinely undecided and will be refined over time.
Two failure modes threaten from opposite directions. Blocking R0 to R3 on visual design puts a
non-thesis concern on the critical path. Letting colours, fonts and spacing accumulate inside
module code guarantees that any later visual decision becomes a diffuse, risky, late refactor
touching every module.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| Design the visual system now | Coherent from day one | Blocks the rungs that carry the marks; will be rewritten once clinicians see R2 |
| Style ad hoc, tidy later | Fastest short term | The later tidy touches every module. This is the classic version of this mistake |
| **Separate the seam: behaviour now, appearance as a swappable bundle** | Neither blocks the other. Late visual work is a bundle, not a refactor. Also enables a teaching variant and a presentation variant from one codebase | Requires discipline up front and a lint to enforce it |

## Decision

**Specify interface behaviour now and package appearance as a swappable UI bundle.**

The governing rule:

> A UI bundle changes how the application looks and how its panes are arranged. It cannot
> change what the application shows, in what order, or with what warning.

Settled now, because it is behaviour and safety rather than appearance: information
architecture, the persistent context bar, the ten interaction contracts, the uncertainty display
rules, the rank-never-suppress rule, and the accessibility floor. See
[`../08-UI_UX_SPEC.md`](../08-UI_UX_SPEC.md).

Deferred into bundles: palette, type, spacing, icons, illustration, density modes, light and
dark variants, colormaps within the declared policy. See
[`../09-UI_BUNDLE_SPEC.md`](../09-UI_BUNDLE_SPEC.md).

## Consequences

**Accepted costs.**
- Discipline is required: no hard-coded colour, font, spacing or icon in any module. This is a
  review checklist item and a rejection reason.
- Modules must declare stable object names as styling hooks.
- The bundle lint must be built early, or the seam erodes quietly.

**What this closes.** Arguments about appearance during R0 to R3. "It looks unfinished" is not
a valid objection to a module; it is a valid objection to the default bundle, later, and there
is now a place to record it.

**What this enables.** Visual identity develops on its own schedule. One codebase serves a
clinical deployment, a teaching deployment and a projector demo. And the seam itself is a small
architectural contribution worth a paragraph in the implementation chapter.

**What a bundle can never do.** Remove the disclaimer, remove the context bar, hide an
information-bearing widget, reorder a ranked list, drop an uncertainty statement, enable motion
for a clinical target, or ship below the accessibility floor. Each is enforced by the lint, in
CI, not by convention.

## Evidence

The platform already supports it: a custom Slicer application is themed with Qt stylesheets set
from CMake variables and resource files. This formalises an existing mechanism rather than
inventing one. The benchmark work independently established why the viewport background in
particular must be pinned rather than themed: a raycast composites the background into every
non-opaque pixel, so three stacks with different default backgrounds produced visibly different
images from identical data.

## Revisit trigger

The lint proves unenforceable in practice, or a clinician session shows that a behaviour
currently fixed in [`../08-UI_UX_SPEC.md`](../08-UI_UX_SPEC.md) genuinely needs to vary by
deployment.
