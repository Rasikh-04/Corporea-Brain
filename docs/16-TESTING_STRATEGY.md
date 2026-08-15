# 16 — Testing strategy

<a id="pyramid"></a>

## The test pyramid here

It is not the usual shape. In a medical imaging application the expensive-to-write,
slow-to-run tests are the ones that actually prevent the failures that matter.

```
        ┌──────────────────────────┐
        │  Offline + release gate  │   rare, manual-triggered, blocking
        ├──────────────────────────┤
        │  Golden-case regression  │   nightly, catches silent drift
        ├──────────────────────────┤
        │  Pipeline integration    │   per PR on a small fixture set
        ├──────────────────────────┤
        │  Module tests in Slicer  │   per PR
        ├──────────────────────────┤
        │  Unit tests (headless)   │   per commit, fast
        └──────────────────────────┘
   Cross-cutting, always: the orientation assertion
                          the metric known-answer test
                          the PHI-in-logs assertion
                          the UI bundle lint
```

The three cross-cutting tests are non-negotiable. Each one catches a failure that is otherwise
**completely silent** and that would invalidate every result downstream of it.

<a id="unit"></a>

## Unit tests

Fast, headless, no Slicer import, no GPU, no data files larger than a few kilobytes.

This is only possible because of the rule in [`14-CODING_STANDARDS.md`](14-CODING_STANDARDS.md):
a scripted module's logic lives in a plain class with no Slicer imports at module import time,
and the widget is a thin shell over it. Enforce that rule and this layer is easy; break it and
this layer is impossible.

Covered here: sequence classification rules, attribution arithmetic, uncertainty computation,
manifest validation, provenance stamping, record store operations, export shaping.

<a id="module"></a>

## Module tests in Slicer

Run inside Slicer's Python interpreter, using its test infrastructure. Covered: node creation
and attribute conventions, scene serialisation round-trip, widget-to-logic wiring, observer
cleanup.

The observer-cleanup test matters more than it sounds: a dangling observer crashes at an
unrelated moment later, which is the hardest class of bug to attribute.

<a id="pipeline"></a>

## Pipeline integration tests

A small committed fixture set — synthetic and public-sample volumes only, never patient data —
run end to end on every PR that touches the pipeline.

Asserted: every stage produces a `DerivedArtifact` with complete provenance; the cache is hit
on a second run; a killed run resumes without recomputing completed stages; each failure class
in the taxonomy is produced by a fixture designed to trigger it.

**Include a deliberately broken fixture per failure class.** A failure path with no test is a
failure path that returns a default in production.

<a id="orientation"></a>

## The orientation assertion test

The most important test in the repository.

A synthetic asymmetric phantom volume, committed, with an unmistakable lopsided marker, pushed
through **every stage that touches geometry**. After each stage, a hard assertion verifies the
marker is on the expected side at the expected voxel and world coordinates.

- Runs in CI on every commit, not on a schedule and not by hand.
- Runs again at application startup in a debug build, writing the result to the log.
- Its output appears in every per-case QC report as a rendered image with laterality burned in.

A left/right flip produces a lesion in the wrong hemisphere, and every downstream output —
attribution, tracts, deficit hypotheses, proximity warnings — is then confidently wrong while
looking completely normal. There is no other control for this.

<a id="golden"></a>

## Golden-case regression

A small set of fixed public cases, processed end to end nightly, with outputs compared against
committed expected values within declared tolerances.

Compared: segmentation Dice against the stored value; the ranked attribution list, both
membership and order; lesion volume; the derived-artifact graph shape; the reproducibility
check that identical input yields byte-identical artifacts.

**Attribution order is part of the assertion.** A change that reorders the ranked list changes
what a clinician reads first, which is a behaviour change even when every number is unchanged.

Tolerances are declared and justified in the test, not tuned until the test passes.

<a id="harness-tests"></a>

## Evaluation harness tests

The harness has its own tests, and it needs them more than most components because a broken
metric produces plausible numbers.

- **Known-answer test: two synthetic masks with a hand-computed Dice.** Write this first, before
  any other harness code. It is the highest-value test in the project.
- Known-answer tests for HD95 and ASSD on simple geometry with analytically derivable answers.
- Degenerate cases: empty prediction, empty ground truth, both empty, single voxel, disjoint
  components. Each must produce a defined result or a defined error, never a silent `NaN`.
- Determinism: the same inputs produce the same table.
- The harness never imports the application. Asserted by a test that fails if it does.

<a id="ui-smoke"></a>

## UI smoke tests

Not exhaustive UI automation, which is expensive and brittle for the value it returns here.
Instead, per screen: it opens, it renders, it does not crash on an empty state, its error state
appears when the underlying operation fails.

Plus the specific safety assertions, which are worth automating because they are exactly what a
late visual change would break:

- The disclaimer is shown before any data can be loaded.
- The context bar is present and shows parcellation and coordinate space on every screen from
  S3 onward.
- The attribution list contains every region with non-zero overlap. No filter control exists.
- A value with no uncertainty is never rendered as a number.
- Teaching-mode cases are visually distinguishable from patient cases.

<a id="offline-test"></a>

## The offline test

Network interface disabled at the OS level, not by trusting the application. Cold start, import
from local media, full pipeline, export. **Any outbound connection attempt is a failure**,
detected at packet level rather than by reading the code.

Manual-triggered, and a release gate. See
[`17-RELEASE_AND_PACKAGING.md`](17-RELEASE_AND_PACKAGING.md).

<a id="perf-gate"></a>

## Performance regression gate

Nightly, and per PR for changes touching rendering or the pipeline.

Because absolute timings on the reference machine are comparable only within one capture batch,
the gate **builds the baseline and HEAD in one shared batch and compares ratios.** An absolute
threshold checked against a nightly number would produce constant false alarms from cross-batch
drift, and the team would then start ignoring it, which is worse than not having it.

Gate: a regression beyond the declared ratio fails the build and names the metric and the
commit. Frame rate figures come only from an attended slot, because a locked session cannot
measure them and the runner correctly refuses to try.

<a id="ci"></a>

## CI layout

| Trigger | Runs |
|---|---|
| Every commit | Unit tests, linters, formatters, **orientation assertion**, **metric known-answer**, **PHI-in-logs assertion**, manifest validator, **UI bundle lint** |
| Every PR | The above, plus module tests, pipeline integration on the fixture set, licence register check, `.gitignore` check for data paths |
| Nightly | Golden-case regression, performance regression with paired baseline, dependency and licence audit |
| Pre-release | Offline test, full evaluation on the declared splits, packaging, the pre-publication audit checklist |

The commit-level set must stay fast. A slow commit gate gets bypassed, and the three
cross-cutting assertions live in it precisely because they must never be bypassed.

<a id="coverage"></a>

## Coverage targets, and where they do not apply

Target 80 percent line coverage on our own C++ and Python. Explicitly **not** applicable to:

- Upstream Slicer, VTK and ITK. Not ours, not our tests.
- Generated code, including the generated Qt stylesheet.
- Thin widget shells, which the architecture deliberately keeps logic-free.
- Model inference internals. We test the wrapper, the metrics and the outputs, not the network.

**Coverage is a smoke detector, not a goal.** A module at 95 percent coverage with no failure
path tested is worse than one at 60 percent that tests every error branch. The review checklist
asks about failure paths for exactly this reason.

---

**Related:** [`06-IMAGING_PIPELINE.md`](06-IMAGING_PIPELINE.md) ·
[`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md) ·
[`14-CODING_STANDARDS.md`](14-CODING_STANDARDS.md) ·
[`09-UI_BUNDLE_SPEC.md`](09-UI_BUNDLE_SPEC.md)
