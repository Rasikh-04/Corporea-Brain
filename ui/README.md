# ui/

UI bundles. Design tokens, generated stylesheets and layout presets.

Specified by [`docs/09-UI_BUNDLE_SPEC.md`](../docs/09-UI_BUNDLE_SPEC.md) and
[ADR-008](../docs/DECISIONS/ADR-008-ui-bundle-seam.md).

## The seam

Visual design is deferred behind this directory. Modules carry no colour, font, spacing, radius
or icon of their own; they read them from the active bundle. That is what lets the visual
design land late without touching module code, and it is why the review checklist in
[`docs/14`](../docs/14-CODING_STANDARDS.md#review) asks about hard-coded visual values on every
pull request.

**Seam 3: UI bundles never contain logic.** Tokens, stylesheets and layout only.

## Bundle anatomy

One directory per bundle under `bundles/<bundle-id>/`, each with `bundle.json`, `tokens.json`
and at least one layout preset. `generated/style.qss` is produced from `tokens.json` and is
never hand-edited. Full structure in
[`docs/09`](../docs/09-UI_BUNDLE_SPEC.md#anatomy).

## What a bundle may never change

A bundle changes how the application looks. It may never change what it says. It cannot alter
which information is displayed, the order of a ranked list, whether an uncertainty statement is
shown, the context bar, the startup disclaimer, the `NEEDS_SOURCE` placeholder, any
accessibility floor, or the visual distinction between teaching-mode and patient cases. The
full table is in [`docs/09`](../docs/09-UI_BUNDLE_SPEC.md#allowed).

The bundle lint enforces this and runs on every commit.

## Status

No bundle exists yet. Nothing in this directory is built. The seam is specified so that module
code written before the design lands is still written correctly.
