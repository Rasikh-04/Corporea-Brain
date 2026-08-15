# organs/

Organ manifests and their assets. One directory per organ, one `manifest.yaml` in each.

Specified by [`docs/04-ORGAN_MODULE_SPEC.md`](../docs/04-ORGAN_MODULE_SPEC.md).

## Why a manifest, and not code

The claim is not "we modelled the human body." It is "we built an organ-agnostic platform and
implemented the brain to depth in it." The manifest is what makes that claim structural rather
than rhetorical: the application reads implementation level from data and displays it, so a
stub organ says "stub" in the UI and nobody can allege over-claiming.

## What lives here

| Path | Holds |
|---|---|
| `brain/manifest.yaml` | The brain, `implementation_level: deep`. |

The schema itself is not a JSON Schema file. It is
[`app/corporea_core/organ_manifest.py`](../app/corporea_core/organ_manifest.py), hand-written,
because [`docs/04`](../docs/04-ORGAN_MODULE_SPEC.md#registration) requires the **specific
failing field** be reported. That module says `geometry.layers[1].mesh is required`, which
sends someone to a line; a schema library says the document did not conform, which sends them
to the file. One definition serves both the application's `OrganRegistry` and CI, because a CI
check that disagrees with the runtime is worse than none, having been trusted.

Assets are **not** committed. `assets/`, `*.glb`, atlases and templates are git-ignored: they
carry their own licences and are fetched, not redistributed. See
[`docs/13-LEGAL_AND_ETHICS.md`](../docs/13-LEGAL_AND_ETHICS.md).

## known_gaps is load-bearing

The field most likely to be treated as optional. It is not.

It is present on every manifest including stubs, because an empty list is a claim that the
geometry is complete and that claim needs evidence. Gaps are discovered by inventorying the
geometry, never by reading the source's description files: Z-Anatomy names structures that
exist only as label leader lines with no surface, and the ear work found that out the
expensive way.

Every gap names the layers it affects and the consequence. "No cerebral veins" is a note. "No
vascular claim of any kind may be made from this model" is a constraint the UI and the report
both honour.

## Validation

```bash
.venv/bin/python scripts/validate_organs.py
```

Runs in CI on every PR. A manifest that fails validation is reported with the specific failing
field and the organ is excluded. It is never silently skipped. CI failure blocks merge.

Two checks in [`docs/04`](../docs/04-ORGAN_MODULE_SPEC.md#validation) cannot run yet and are
reported as deferred rather than omitted: parcellation ids resolve against
[ADR-006](../docs/DECISIONS/ADR-006-coordinate-space-and-atlas.md), which is open, and disorder
ids resolve against a catalog that does not exist yet.
