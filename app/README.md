# app/

The custom 3D Slicer application and the modules we write for it.

Specified by [`docs/03-ARCHITECTURE.md`](../docs/03-ARCHITECTURE.md) and
[ADR-003](../docs/DECISIONS/ADR-003-application-shell.md).

## What lives here

| Path | Holds | Status |
|---|---|---|
| `corporea_core/` | Pure Python shared between Slicer modules and headless tooling | present |
| `<AppName>/` | SlicerCustomAppTemplate output: branding, home module, curated module set | not built, needs the superbuild |
| `Modules/` | Our scripted and loadable modules, one directory each | not built, needs the superbuild |

Everything except `corporea_core/` is blocked on the Slicer superbuild, which is deferred.
See [`docs/15-BUILD_AND_ENVIRONMENT.md`](../docs/15-BUILD_AND_ENVIRONMENT.md).

## corporea_core

The rule in [`docs/14-CODING_STANDARDS.md`](../docs/14-CODING_STANDARDS.md): a scripted
module's logic lives in a plain class with no Slicer imports at module import time, and the
widget is a thin shell over it. `corporea_core` is where that logic goes when it is also
needed by something outside Slicer, such as a CI script.

**It imports no `slicer`, `vtk`, `ctk`, `qt` or `PythonQt` at import time.** That constraint
is what makes the unit test layer possible at all, so it is asserted by a test rather than
trusted: `app/tests/test_no_slicer_imports.py`.

## Seams that apply here

From [`docs/03-ARCHITECTURE.md`](../docs/03-ARCHITECTURE.md#seams):

1. Organ modules never write to the record store directly. They go through the body layer.
2. The record store never imports an organ module.
5. No module hard-codes a parcellation, an atlas, or a coordinate space. Those come from
   configuration resolved by [ADR-006](../docs/DECISIONS/ADR-006-coordinate-space-and-atlas.md),
   which is open. Until it closes, the placeholders are `<CANONICAL_SPACE>` and
   `<PARCELLATION>`.
