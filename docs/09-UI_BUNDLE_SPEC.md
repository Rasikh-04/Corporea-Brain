# 09 — UI bundle specification

The theming seam. This is how visual identity gets packaged separately from behaviour, so
functionality ships first and appearance is polished later without a redesign touching module
code.

Decision and rationale: [ADR-008](DECISIONS/ADR-008-ui-bundle-seam.md).
Behaviour this must not violate: [`08-UI_UX_SPEC.md`](08-UI_UX_SPEC.md).

<a id="the-seam"></a>

## The seam and the rule that defines it

> **A UI bundle changes how the application looks and how its panes are arranged. It cannot
> change what the application shows, in what order, or with what warning.**

Everything that follows is a consequence of that one sentence. If a proposed bundle feature
would let a bundle hide a finding, reorder a ranked list, drop an uncertainty statement or
remove the disclaimer, the answer is no, and the feature does not go in the schema.

Why this seam and not a conventional "we'll style it later":

1. **Slicer already gives it to us.** A custom Slicer application is themed with Qt
   stylesheets set from CMake variables and resource files. We are formalising a mechanism the
   platform already has, not inventing one.
2. **It de-risks the schedule.** R0 through R3 are behaviour. Visual design has a different
   critical path, needs clinician contact to get right, and would otherwise block or be
   blocked.
3. **It makes "unfinished-looking" a non-blocking objection** during the rungs that carry the
   marks, while giving that objection a real place to go.
4. **It is itself a small architectural contribution** worth a paragraph in the implementation
   chapter, because it is what lets one codebase serve a clinical deployment, a teaching
   deployment and a demo without forking.

<a id="anatomy"></a>

## Bundle anatomy

One directory per bundle under `ui/bundles/<bundle-id>/`.

```
ui/bundles/clinical-dark/
├── bundle.json          required   manifest and metadata
├── tokens.json          required   the single source of visual values
├── layouts/             required   at least one layout preset
│   ├── default.json
│   ├── compact.json
│   └── reading.json
├── icons/               optional   SVG only, monochrome, currentColor
├── colormaps/           optional   overlay colormaps, must pass the policy below
└── generated/           built      style.qss produced from tokens.json — never hand-edited
```

`bundle.json`:

```json
{
  "bundle_id": "clinical-dark",
  "display_name": "Clinical Dark",
  "schema_version": 1,
  "author": "Corporea-Brain",
  "licence": "Apache-2.0",
  "targets": ["clinical", "demo"],
  "base_variant": "dark",
  "default_layout": "default",
  "min_app_version": "0.1.0"
}
```

<a id="tokens"></a>

## tokens.json schema

The single source of every visual value. No module ever hard-codes any of these. There is no
second place a colour may live.

```json
{
  "schema_version": 1,
  "colour": {
    "surface":        { "base": "#1b1e21", "raised": "#24282c", "sunken": "#141618" },
    "viewport":       { "background": "#000000" },
    "text":           { "primary": "#e8eaed", "secondary": "#9aa0a6", "disabled": "#5f6368" },
    "border":         { "subtle": "#2f343a", "strong": "#454b52" },
    "accent":         { "base": "#4a9eff", "hover": "#6cb0ff", "pressed": "#3a86e0" },
    "state":          { "info": "#4a9eff", "caution": "#e0a030", "critical": "#e05252", "ok": "#3fa860" },
    "confidence":     { "high": "#3fa860", "moderate": "#e0a030", "low": "#8a8f94" },
    "focus":          { "ring": "#ffd24a" }
  },
  "type": {
    "family":  { "ui": "system-ui", "mono": "monospace" },
    "size":    { "xs": 11, "sm": 12, "base": 13, "lg": 15, "xl": 18 },
    "weight":  { "regular": 400, "medium": 500, "bold": 700 },
    "line":    { "tight": 1.2, "base": 1.45 }
  },
  "space":  { "0": 0, "1": 2, "2": 4, "3": 8, "4": 12, "5": 16, "6": 24, "7": 32 },
  "radius": { "none": 0, "sm": 2, "md": 4 },
  "target": { "min_pointer_px": 28 },
  "motion": { "enabled": false, "duration_ms": 0 }
}
```

Notes that are requirements, not commentary:

- **`colour.viewport.background` defaults to `#000000` and a bundle that changes it must
  declare why.** Radiological reading is done on black; more importantly, a raycast composites
  the background into every non-opaque pixel, so changing it changes the rendered image, not
  just the frame around it. The stack benchmark established this the hard way when three
  candidate stacks produced visibly different images from identical data purely because their
  default backgrounds differed.
- **`motion.enabled` defaults to `false`.** Motion adjacent to a diagnostic image is a
  distraction with a clinical cost (IC-08). A bundle may enable it for a teaching or demo
  target; it may not enable it for a `clinical` target.
- **`confidence` colours are a convenience, never the sole encoding.** Confidence is always
  also encoded by ordering or a non-colour cue.

<a id="qss"></a>

## Qt stylesheet generation

`generated/style.qss` is produced from `tokens.json` by `scripts/build_ui_bundle.py`. It is
built, committed for reproducibility, and **never hand-edited**. A hand edit is detected by
checksum and fails the lint.

Rules:

- Selectors target Qt classes and object names only. No selector may depend on a widget's
  position in a layout, because layout is a preset and may change.
- Any widget a module needs to style differently gets a stable `objectName`, declared in the
  module and documented. Modules declare hooks; bundles use them.
- No stylesheet rule may set `visibility` or `max-height: 0` on anything carrying information.
  That would be hiding a finding through the back door, and the lint checks for it.

<a id="layouts"></a>

## Layout presets

A layout preset arranges the three zones from
[`08-UI_UX_SPEC.md`](08-UI_UX_SPEC.md#ia) — navigator, stage, detail — plus the context bar
and status bar. It sets sizes, ratios, docking and default visibility of optional panes.

```json
{
  "layout_id": "default",
  "display_name": "Default",
  "context_bar": { "visible": true, "locked": true },
  "zones": {
    "navigator": { "side": "left",  "width_ratio": 0.20, "collapsible": true },
    "stage":     { "width_ratio": 0.55 },
    "detail":    { "side": "right", "width_ratio": 0.25, "collapsible": false }
  },
  "status_bar": { "visible": true, "locked": true },
  "per_screen": {
    "S5": { "detail": { "width_ratio": 0.32 } },
    "S7": { "navigator": { "collapsed": true } }
  }
}
```

`context_bar.locked` and `status_bar.locked` are `true` in every shipped bundle and the lint
enforces it. Those bars carry the parcellation, the coordinate space and the disclaimer. They
are not decoration.

<a id="icons"></a>

## Icon set

SVG only. Monochrome, drawn with `currentColor` so a single asset serves every variant. Fixed
canvas, consistent optical weight. Every icon has a text label or an accessible name — an icon
is never the only carrier of meaning, which follows directly from the no-colour-alone and
no-information-by-glyph-alone rules.

If a bundle omits an icon, the default bundle's icon is used. Missing icons degrade; they do
not break.

<a id="colormaps"></a>

## Colormap policy for clinical overlays

This is the one part of a bundle with a real clinical consequence, so it has hard rules rather
than guidance.

1. **Perceptually uniform.** No rainbow, no jet. Non-uniform colormaps invent structure that is
   not in the data, and radiology has been burned by this repeatedly.
2. **Colourblind-safe** under deuteranopia, protanopia and tritanopia simulation. Checked by
   the lint, not by eye.
3. **Monotonic in lightness** for any map representing a continuous quantity, so it survives
   greyscale printing and a bad projector.
4. **Categorical maps are for categories only** — lesion sub-labels such as necrotic core,
   oedema and enhancing tumour — and are limited to a small, distinguishable set.
5. **Overlay masks carry a second visual channel**: an outline or a hatch in addition to fill,
   so mask extent is legible without colour at all.
6. **Every colormap declares its intended semantic** in a sidecar. A map intended for a
   continuous quantity cannot be assigned to a categorical overlay.

<a id="allowed"></a>

## What a bundle may and may never change

| May change | May never change |
|---|---|
| Colours, type, spacing, radius | Which information is displayed |
| Icons and illustration | The order of a ranked list |
| Zone ratios, docking, collapsibility | Whether an uncertainty statement is shown |
| Which optional panes are open by default | The context bar or status bar contents or presence |
| Density and default layout preset | The startup disclaimer or the not-for-clinical-use banner |
| Colormaps, within the policy above | The pending-review banner |
| Motion, only for non-clinical targets | The `NEEDS_SOURCE` placeholder |
| Window chrome and branding | Any accessibility floor value |
| Light or dark variant | Any interaction contract IC-01 to IC-10 |
| | The teaching-mode visual distinction from patient cases |

<a id="loading"></a>

## Loading and switching bundles

- The active bundle is application configuration, resolved at startup, defaulting to
  `clinical-dark`.
- Switching requires a restart in v1. Live switching is a nice-to-have with no evaluated value.
- **A bundle that fails validation is not loaded.** The application falls back to the default
  bundle, tells the user which bundle failed and which check failed, and continues. It never
  starts unstyled and it never starts silently on a fallback.
- Bundles are data. Loading one must not be able to execute code. No scripting in a bundle, no
  exceptions — a bundle is a plausible attack surface on a machine holding patient data.

<a id="default"></a>

## The default bundle

`clinical-dark` ships with the application and is the reference implementation of this
specification. It is deliberately plain: dark, dense, high-contrast, no ornament, black
viewport, motion off. It is not a placeholder to be embarrassed about. It is what the
application should look like in a clinic, and any successor has to argue against it on
function.

Planned siblings, none of which are on the critical path:

| Bundle | Target | Differences |
|---|---|---|
| `clinical-light` | Clinics with bright rooms and printing | Light chrome, viewport stays black |
| `teaching` | Trainees, S10 | Visually distinct from patient cases by requirement; roomier density; motion permitted |
| `presentation` | Demo, viva, projector | Larger type, higher contrast, thicker overlay outlines |

<a id="lint"></a>

## Bundle lint

`scripts/lint_ui_bundle.py`, run in CI on every bundle on every PR. Checks:

- schema conformance of `bundle.json`, `tokens.json` and every layout preset
- **every token referenced by the generated stylesheet exists** and every token is used
- text contrast ≥ 4.5:1 and meaningful non-text ≥ 3:1, computed, for every foreground and
  background pair the stylesheet actually produces
- every colormap passes the perceptual uniformity and colourblind checks
- `context_bar.locked` and `status_bar.locked` are true
- no rule hides an information-bearing widget
- `generated/style.qss` matches a fresh build from `tokens.json`
- `motion.enabled` is false for any bundle with a `clinical` target
- every icon has an accessible name

**A bundle that fails lint cannot merge.** This is what makes the accessibility floor a floor
rather than an intention.

<a id="open"></a>

## Open questions

Recorded so the thinking is visible and can be resumed. None of these block R0 to R3.

1. **Should layout presets be per-user rather than per-bundle?** IC-07 says layout must not
   move between sessions unless the user moved it, which implies user overrides layered on top
   of the preset. Probably yes. Needs a decision before S5 is built.
2. **How much of Slicer's own chrome should the bundle reach?** A custom app can restyle the
   Slicer shell, but the further we reach the more we couple to upstream internals. Current
   position: style our modules fully, style the shell lightly, never patch upstream.
3. **Where does per-organ visual identity live** if the ear module wants a different accent?
   Current position: it does not. One bundle, one identity, organs differ by content.
4. **Does the presentation bundle risk misrepresenting results in the viva** by exaggerating
   overlay contrast? Probably yes. It may need a visible watermark stating that display
   parameters differ from clinical defaults.
5. **Density modes need a clinician session to choose defaults.** Deferred until after the
   first usability session, per NFR-05.

---

**Related:** [`08-UI_UX_SPEC.md`](08-UI_UX_SPEC.md) ·
[`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md) ·
[`16-TESTING_STRATEGY.md`](16-TESTING_STRATEGY.md) ·
[ADR-008](DECISIONS/ADR-008-ui-bundle-seam.md)
