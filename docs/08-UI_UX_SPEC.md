# 08 — UI/UX specification

<a id="position"></a>

## The design position

Clinical software is not ugly by accident. It is dense, unfashionable and stable because the
people using it are doing something else — thinking about a patient — and the interface has to
get out of the way. Radiological reading happens on black. Layouts stay put between sessions
because muscle memory is faster than discovery. Nothing animates, because motion in the
periphery of a diagnostic image is a distraction with a clinical cost.

So this specification is deliberately **function first**:

> Specify what the interface must *do*, what it must *never* do, and how information is
> arranged and prioritised. Do not specify what it looks like. Appearance ships later, as a
> swappable bundle, and cannot change behaviour.

That seam is [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md) and
[ADR-008](DECISIONS/ADR-008-ui-bundle-seam.md). It exists so that the visual identity — which
is still being worked out and will be refined — can be developed on its own schedule without
blocking R0 through R3, and without a late redesign touching module code.

**Three consequences, stated so nobody has to re-derive them:**

1. A pull request that changes a colour, a font, a spacing value or an icon inside a module is
   rejected. Those belong in a bundle.
2. A pull request that changes what information is shown, in what order, or with what warning
   is a **behaviour** change and needs a review against this document.
3. "It looks unfinished" is not a valid objection to a module during R0 to R2. It is a valid
   objection to the default bundle, later, and there is a place to record it.

<a id="inventory"></a>

## Screen inventory

Ten screens. Nothing else exists without an ADR.

| # | Screen | Primary user | Rung | Time budget |
|---|---|---|---|---|
| S1 | Case list | All | R0 | < 10 s to find a patient |
| S2 | Ingest and QC | All | R0 | < 2 min per study, including corrections |
| S3 | Body shell | All | R1 | < 5 s to reach the brain |
| S4 | Brain atlas | Trainee, neurologist | R1 | Unbounded |
| S5 | Case workspace | Neurologist, radiologist | R2 | **The screen that must work in 5 min** |
| S6 | Attribution and hypotheses | Neurologist, surgeon | R2 | < 2 min to read |
| S7 | Timeline | Neurologist | R2 | < 1 min to answer "has it changed" |
| S8 | Trajectory planner | Surgeon | R3 | 10 to 30 min |
| S9 | Report and export | All | X | < 1 min |
| S10 | Teaching mode | Trainee | X | Unbounded |

<a id="ia"></a>

## Information architecture

Three persistent zones, present on every screen from S3 onward. Their **positions are fixed by
the layout preset in the active bundle; their contents are fixed by this document.**

```
┌──────────────────────────────────────────────────────────────────────┐
│  CONTEXT BAR   patient · study date · active organ · parcellation ·  │
│                coordinate space · [PENDING REVIEW] · [NOT FOR        │
│                CLINICAL USE]                                         │
├───────────────┬──────────────────────────────────────┬───────────────┤
│  NAVIGATOR    │  STAGE                               │  DETAIL       │
│  what exists  │  the thing under examination         │  what is true │
│  and where    │  (image, mesh, timeline, form)       │  about the    │
│  you are      │                                      │  selection    │
├───────────────┴──────────────────────────────────────┴───────────────┤
│  STATUS  pipeline stage · QC state · cache state · long-job progress │
└──────────────────────────────────────────────────────────────────────┘
```

**The context bar is never scrolled away, never collapsed and never themed out of
existence.** It carries the two statements a user must never have to go looking for: which
atlas and space produced the labels they are reading, and that this is not a clinical device.

<a id="navigation"></a>

## Navigation model

Body shell → organ → case → analysis. Depth-first, always reversible, never modal.

- **No modal dialogs for anything that takes longer than a second.** Long work runs in the
  status zone with progress and a cancel.
- **Back always works and never loses state.** Returning to a screen restores selection,
  camera and scroll position.
- **The full Slicer module list is reachable but not on the path.** One explicit "Advanced"
  affordance. A clinician should never meet the researcher toolkit by accident; a trainee
  should be able to find it deliberately.

<a id="s1"></a>

## S1 — Case list

Rows: patient identifier, age band, sex, handedness, most recent study date, number of
studies, active disorder, review status.

Sort and filter on every column. Search matches identifier and disorder. Handedness is on the
list, not buried in a detail panel, because it changes interpretation.

Empty state names the action: "No cases. Import a study from a folder, USB or CD."

<a id="s2"></a>

## S2 — Ingest and QC

Two panes. Left: the series tree as found. Right: the QC report.

Per series the tree shows: raw `SeriesDescription` verbatim, the classified sequence, the
confidence, and the method (rule, learned, manual). **The raw description is always visible
next to the guess.** A user must be able to see what the system saw.

Correction is one control per row, always enabled, never hidden behind an edit mode. Correcting
sets the record's `corrected_by_user` flag and writes to the audit log.

The QC report is not a link. It is the right-hand pane, open by default, with the orientation
panel at the top — including the rendered laterality check image. A failing QC panel shows a
blocking banner with the specific failed check and an explicit override control that logs who
overrode what.

<a id="s3"></a>

## S3 — Body shell

A navigable shell model and an organ picker. Every organ carries an implementation-level
badge: **deep**, **shallow**, **stub**. A stub organ, when selected, renders its mesh, its
name and the literal text "Not implemented in this release." It never renders an empty
analysis panel.

This screen is where the honesty of the whole-body claim is visible. It is worth thirty
seconds of the demo for exactly that reason.

<a id="s4"></a>

## S4 — Brain atlas

Navigator: hierarchical structure tree, system → structure → substructure, searchable with
synonyms. Stage: the 3D model with layer toggles. Detail: the selected structure.

**Bidirectional selection is required.** Clicking a mesh highlights the tree node; selecting a
tree node highlights the mesh. Neither direction may be the slow one.

Layer toggles: cortex, deep grey, ventricles, white-matter tracts, vasculature. **Toggling a
layer that carries a `known_gaps` entry surfaces that entry inline, at the toggle, not in an
About dialog.** Toggling vasculature shows "Dural sinuses only. Cerebral veins absent. No
vascular claim may be made from this model."

Descriptions: linked out, never authored. A structure with no cited description renders
`NEEDS_SOURCE` as a visible pending placeholder.

<a id="s5"></a>

## S5 — Case workspace

The screen that has to work inside a five-minute consult. Everything here is subordinate to
that constraint.

Default layout on open, in priority order top to bottom in the detail zone:

1. **What changed since last visit** — one line, quantitative, or "No prior study."
2. **Current lesion volume** with uncertainty and the trend arrow.
3. **Top three involved regions** with overlap percentage, and a control to expand the full
   ranked list.
4. **Any active flag** — mass effect detected, handedness unknown, QC overridden, degraded
   stage.

Stage zone: 2D orthogonal views with the mask overlay, window and level, and a 3D view.

**The first thing on screen answers the question the clinician actually walked in with.** It
is not a viewer that happens to have numbers attached; it is an answer that happens to have a
viewer attached.

<a id="s6"></a>

## S6 — Attribution and hypotheses

Two stacked tables.

**Attribution table.** One row per involved region: region name, role (primary or secondary),
overlap as a percentage of the region, overlap as a percentage of the lesion, rank, and the
uncertainty statement. Sorted by rank. **Every region with non-zero overlap is present.** There
is no "show more relevant only" control, because that control is the thing the clinician told
us not to build.

**Hypotheses table.** One row per expected correlate: the correlate, the source region or
tract, the confidence band, and the citation as a resolvable link. Header text, always
present and never themed away: *"Expected correlates from the literature. These are
hypotheses, not findings, and not a diagnosis."*

Where a region's geometry was substituted because the true site has no surface in the atlas,
the row says so explicitly and names the substitution.

<a id="s7"></a>

## S7 — Timeline

One horizontal axis: time. Lanes, top to bottom: studies, lesion volume trend, scores,
medications, events. Selecting any two points opens the comparison view.

**The timeline is the differentiator.** Nothing else puts imaging quantification and the
clinical record on one axis. It gets the space it deserves and it is in the demo.

Genogram lives here as a separate view, not a separate screen: standard symbols, squares for
male and circles for female, filled for affected, with a legend that is always visible because
genogram convention is not universal.

<a id="s8"></a>

## S8 — Trajectory planner

Entry and target placement on the patient volume, trajectory line with length and angle, and a
probe-eye view down the trajectory axis.

**Structures-along-path**: the ordered list of every structure the trajectory traverses, with
entry and exit depth in millimetres. This is the concrete artifact no free tool hands you and
it is the reason the screen exists.

**Eloquent proximity**: minimum distance from the trajectory to each eloquent region and each
critical tract, ranked, with a configurable threshold. Ranked, not filtered.

Multi-trajectory comparison: two or three candidates side by side on traversed structures and
minimum eloquent distance.

Persistent banner: *"Pre-operative planning support on imaging only. Not navigation, not
intra-operative, no clinical claim."*

<a id="s9"></a>

## S9 — Report and export

A preview of exactly what will be produced, then the export. No surprises between preview and
file. The provenance footer and the disclaimer are visible in the preview, not added silently
at write time.

<a id="s10"></a>

## S10 — Teaching mode

Separate case library, visually distinct from patient cases so the two can never be confused —
this is one of the few places where a visual difference is a **safety** requirement and is
therefore specified here rather than left to a bundle. The bundle chooses how; this document
requires that.

Guided walkthrough: history, then imaging, then attribution, with the answer revealed after
the learner commits.

<a id="contracts"></a>

## Interaction contracts

These are behavioural requirements. A bundle cannot change them.

| # | Contract |
|---|---|
| IC-01 | Selection is bidirectional wherever a list and a geometry both represent the same thing. |
| IC-02 | No operation longer than one second blocks the UI. It runs with progress and a cancel. |
| IC-03 | Cancel leaves the system in a valid state and loses no completed work. |
| IC-04 | Every destructive action is reversible or requires typed confirmation. Never both absent. |
| IC-05 | Every error names the failure class and the specific input responsible. Never "an error occurred." |
| IC-06 | State survives navigation. Returning to a screen restores selection, camera and scroll. |
| IC-07 | Layout does not move between sessions unless the user moved it. |
| IC-08 | Nothing animates in or adjacent to a diagnostic image. |
| IC-09 | Every derived number displays its unit and its uncertainty in the same visual unit as the number. |
| IC-10 | Every label displays, or is one hover from, the atlas and space that produced it. |

<a id="uncertainty"></a>

## Uncertainty and confidence display rules

The rules that keep the system honest at the pixel level.

1. **A number with no uncertainty is not rendered as a number.** It is rendered as a
   qualitative statement, or not at all. There is no third option.
2. **Uncertainty is adjacent, never in a tooltip.** A tooltip is opt-in, and the whole point is
   that this is not opt-in.
3. **Three confidence bands only: high, moderate, low.** Not percentages, unless the number is
   genuinely a calibrated probability — which model softmax outputs generally are not. Do not
   render a softmax value as a confidence percentage.
4. **The band is encoded twice**, once by position or ordering and once by a non-colour cue.
   Colour alone fails for colourblind users and fails again on a projector.
5. **`NEEDS_SOURCE` renders as a visible pending placeholder.** Never blank, never substituted,
   never quietly omitted from the list.
6. **Model confidence and clinical confidence are never shown in the same visual language.**
   They are different kinds of claim and conflating them is the most likely way this interface
   misleads someone.

<a id="alerting"></a>

## Alerting and the rank-never-suppress rule

The clinician said missing something is far worse than over-flagging. That determines the
operating point, and it creates a real tension with alert fatigue. The resolution, stated once
so it is not re-argued:

> **Display everything. Rank it. Never hide it. Never interrupt for it.**

- No finding is filtered out of a list, at any threshold.
- Ranking is by a stated, documented criterion, visible to the user.
- Alerts are **passive**: they appear in place, in the relevant zone. Nothing modal, nothing
  that must be dismissed, nothing that blocks the next action.
- The user may collapse the tail of a ranked list. The system may not collapse it by default,
  and a collapsed tail always shows its count.
- The chosen operating point on the sensitivity-specificity curve is documented in the report
  with its justification, per NFR-07.

<a id="states"></a>

## Error, empty and loading states

Every screen specifies all three. A screen without them is not finished.

- **Empty** names the action that fills it. Never just "No data."
- **Loading** shows what is loading and roughly how long. A spinner with no label is not a
  loading state.
- **Error** names the failure class from the pipeline taxonomy, the specific input, and the one
  action available. `INSUFFICIENT_INPUT` says which series is missing and what it was needed
  for — it never silently substitutes a weaker proxy, and the UI says so.

<a id="a11y"></a>

## Keyboard and accessibility floor

Not aspirational. This is the floor and it is checkable.

- Every action reachable by keyboard. Visible focus indicator at all times.
- Tab order follows the visual order of the three zones.
- No information conveyed by colour alone, anywhere. This includes overlay masks, which carry a
  pattern or an outline in addition to a fill.
- Minimum contrast 4.5:1 for text, 3:1 for meaningful non-text. The bundle lint enforces it, so
  a bundle physically cannot ship below the floor.
- Target size floor for pointer targets, honouring that some users work on a laptop trackpad in
  a clinic.
- Text scales without truncation or overlap at 125 percent and 150 percent.

<a id="density"></a>

## Density and the five-minute consult

The grounding clinic runs Tuesday and Thursday, 10:00 to 12:00. Do the arithmetic: that is a
small number of minutes per patient, and the application competes with the patient for the
clinician's attention.

Design rules that follow:

- **S5 answers the question above the fold.** No scrolling to reach "what changed."
- **Structured entry is time-boxed and measured**, not assumed. F5.7 sets three minutes for
  core history and NFR-05 makes learnability a measured requirement.
- **Never require an input the clinician cannot supply in the room.** Physical scores like GCS
  need in-person evaluation and are entered, not administered by the app; cognitive
  questionnaires can be administered in-app.
- **Prefer one dense screen over three sparse ones.** Navigation costs more than density in
  this setting.

<a id="not-yet"></a>

## What is deliberately not designed yet

Recorded so the gap reads as a decision rather than an oversight.

| Deferred | Why | Where it will land |
|---|---|---|
| Visual identity: palette, type scale, spacing, icon style | Function first; the idea is still being refined and will be polished | [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md), default bundle |
| Illustration and empty-state art | Zero evaluated value before R2 | Default bundle, after R2 |
| Onboarding and first-run tour | Cannot be designed before NFR-05 is measured | After the first usability session |
| Localisation | No confirmed second-language requirement | Strings are externalised from day one so it stays cheap |
| Density modes (compact and comfortable) | Needs a real clinician session to choose defaults | Layout presets in the bundle |
| Dark and light variants | Radiological convention is dark; a light variant is a bundle | Default bundle |

**What is *not* deferred:** everything above this section. Information architecture, the
context bar, the interaction contracts, the uncertainty rules, the rank-never-suppress rule and
the accessibility floor are behaviour and safety. They are settled now, before code, because
retrofitting them costs more than writing them.

---

**Related:** [`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md) ·
[`07-SRS.md`](07-SRS.md) ·
[`04-ORGAN_MODULE_SPEC.md`](04-ORGAN_MODULE_SPEC.md) ·
[ADR-008](DECISIONS/ADR-008-ui-bundle-seam.md)
