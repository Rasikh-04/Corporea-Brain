# HANDOFF

Rolling state file. Anyone, human or agent, must be able to resume cold from this page.
Overwrite it; do not append a history. History lives in git and in `docs/DECISIONS/`.

## Last updated

2026-08-16 — Phase 2 started: CI and linting are wired and green (Phase 2 items 1 and 2,
below). Phase 1 scaffolding was already complete and the environment green. The orientation
assertion, the evaluation harness and the organ manifest validator all exist and pass;
`check-env.sh` reports 0 fail. Still no application code, and that is on plan.

## Where the project is

The measuring instruments are built and the thing they measure is not, which is the ordering
rule 7 demands. 176 tests pass in about two seconds against `pytest.ini`.

The two planning documents are settled at version 1 and mirrored under
[`docs/research/`](docs/research/). The document set is complete and indexed at
[`docs/00-INDEX.md`](docs/00-INDEX.md).

What landed in phase 1, in the order it was built:

1. **Directory skeleton.** `app/`, `organs/`, `pipeline/`, `eval/`, `bench/`, `ui/`,
   `hardware/`, `scripts/`, each with a `README.md` naming what it holds and which document
   specifies it.
2. **The orientation assertion.** [`pipeline/braintwin_pipeline/orientation.py`](pipeline/braintwin_pipeline/orientation.py)
   and [`phantom.py`](pipeline/braintwin_pipeline/phantom.py). The one idea it encodes: **the
   assertion is made in world space, never in voxel space.** A test proves why, by showing
   that a correct reorientation to LAS and a broken flip along i produce *byte-identical
   arrays* and differ only in the affine. Any voxel-index check fails the safe operation and
   passes the fatal one. The phantom is checked against all 48 possible storage orders, and
   against a deliberately broken fixture per axis.
3. **The evaluation harness.** [`eval/braintwin_eval/metrics.py`](eval/braintwin_eval/metrics.py):
   Dice, HD95, ASSD, volume error, distances in millimetres. Every expected value in
   `test_metrics_known_answer.py` was computed by hand and the arithmetic is in the docstring.
   No metric returns a bare float; each carries a degeneracy flag, and
   [`aggregate.py`](eval/braintwin_eval/aggregate.py) refuses to average over undefined values
   without being told which policy applies.
4. **The organ manifest schema and validator.** [`app/braintwin_core/organ_manifest.py`](app/braintwin_core/organ_manifest.py),
   run by [`scripts/validate_organs.py`](scripts/validate_organs.py). Collects every issue with
   a dotted field path rather than stopping at the first. Four of the seven checks in docs/04
   run; three are reported `DEFERRED` with the reason, never omitted.

Three architectural seams are now asserted mechanically rather than by review: seam 4 (the
harness never imports the application), the no-Slicer-imports rule for `braintwin_core`, and
seam 5 (the brain manifest carries `<PARCELLATION>`, not an atlas name).

`scripts/check-env.sh` steps 4, 5 and 6 now run the real tests instead of printing SKIP.

**The environment is green.** `scripts/setup-env.sh` finished, and `scripts/check-env.sh`
reports **0 fail, 3 warn** in `.venv`, with steps 4, 5 and 6 passing there.
`pipeline/requirements.lock.txt` is committed: 103 packages, exact.

The three remaining warns are known and unchanged: 15 GiB RAM against a 16 GiB minimum, Fedora
44's CMake 4.x, and a system Qt on `PATH`. All three matter only to the superbuild, and all
three are in the table in [`docs/15`](docs/15-BUILD_AND_ENVIRONMENT.md).

### What check-env.sh caught on its first real run

It earned itself immediately. The requirements install had **silently replaced torch
2.8.0+cpu with 2.13.0+cu130**, pulling 16 nvidia packages and taking `.venv` to 5.8 GB.

The cause is worth remembering, because it will recur. `setup-env.sh` installed torch from the
CPU-only index *first*, and a comment claimed that ordering meant the resolver could not pull
the CUDA build. It does not: pip upgrades an already-installed package whenever a later
requirement permits a newer one, and nnunetv2's `torch>=2.1.2,!=2.9.*` permits a great deal.

Nothing else would have caught it. Every package imported, every test passed, and the only
symptom was disk on a machine already short of the superbuild's 60 GB.

Fixed by [`pipeline/constraints.txt`](pipeline/constraints.txt), an exact pin including the
`+cpu` local version, which the resolver cannot upgrade past. `check-env.sh` now hard-fails on
a non-CPU torch rather than warning, and separately counts `nvidia-*` packages, because pip
does not remove packages that stop being needed and torch's version string can read correctly
while an orphaned CUDA tree sits on disk. Cleanup reclaimed 3.8 GB: `.venv` is 2.0 GB and free
disk went from 33 GB to 36 GB.

## Decisions that are closed

| # | Decision | Where |
|---|---|---|
| ADR-001 | Thesis is T-B, lesion to region to deficit, inside the T-A product frame | [ADR-001](docs/DECISIONS/ADR-001-thesis-scope.md) |
| ADR-002 | Ear is a separate deliverable, out of evaluated FYP scope | [ADR-002](docs/DECISIONS/ADR-002-brain-ear-split.md) |
| ADR-003 | Application shell is a custom 3D Slicer app, Qt/C++/VTK | [ADR-003](docs/DECISIONS/ADR-003-application-shell.md) |
| ADR-008 | Visual design is deferred behind a UI bundle seam | [ADR-008](docs/DECISIONS/ADR-008-ui-bundle-seam.md) |
| ADR-009 | Web POC is retained only as an optional VR viewer, zero analysis logic | [ADR-009](docs/DECISIONS/ADR-009-web-poc-disposition.md) |

## Decisions that are open and blocking

| # | Decision | Blocks | Owner | Deadline |
|---|---|---|---|---|
| ADR-006 | Canonical coordinate space and parcellation atlas | The entire imaging pipeline | Imaging | before any R0 code |
| ADR-004 | Primary user | SRS user stories, screen priority | Lead | end of Phase 0 |
| ADR-005 | Cognitive instrument, MMSE is licence-blocked | Clinical record F5 | Governance | end of Phase 1 |
| ADR-007 | Record store technology | Data model implementation | Backend | before R2 |

## Settled: the phantom is generated, not committed

Raised as a deviation and closed on 2026-08-16. The phantom is a deterministic generator,
written out on demand by [`scripts/make_phantom.py`](scripts/make_phantom.py) into git-ignored
`build/`, and [`docs/06`](docs/06-IMAGING_PIPELINE.md#orientation) and
[`docs/16`](docs/16-TESTING_STRATEGY.md#orientation) have been amended to match rather than
left disagreeing with the code.

The reasoning is in docs/06 in full: `.gitignore` blocks every imaging extension on purpose and
an exception for a fixture is the gap its own header warns about; a generator is auditable
where a binary is not; a committed fixture can drift with nothing to say so; and with no random
seed anywhere, reproducibility is preserved rather than traded away.

The same amendment fixed a second and more consequential disagreement. Both documents said the
assertion checks "the expected voxel and world coordinates." It checks **world coordinates
only**, and the voxel half was actively wrong: a correct reorientation and a catastrophic flip
produce byte-identical arrays, so a voxel-index check fails the safe operation and passes the
fatal one. Written as it was, the document would have led someone to build the wrong test.

## Immediate next actions

1. **Run the orientation exercise by hand, once, and write it down.** This is the highest
   value item on the list and it is now cheap, because the tooling exists.
   `scripts/make_phantom.py --out build/phantom.nii.gz`, then the same with
   `--break-axis 0`. Open both in three independent tools, verify left is left, record how
   you verified it, and note how little there is to see in the broken one. Then do it again
   with one real DICOM study through `dcm2niix`. [`docs/06`](docs/06-IMAGING_PIPELINE.md#orientation)
   asks for this explicitly and it becomes a CI test.
2. **Close ADR-006.** Now the top blocker. The brain manifest carries `<PARCELLATION>`, the
   pipeline cannot name a space, and every deferred check in `validate_organs.py` points at
   it. Nothing in the pipeline can be written correctly before it closes.
3. Slicer superbuild, **still deferred on disk and still not blocking**. 36 GB free against
   a 60 GB minimum, and `~/Projects` is 18 GB of largely stale archives. When disk is freed,
   gate with `scripts/check-env.sh --superbuild` before configuring. `<PINNED_REVISION>` in
   [`docs/15`](docs/15-BUILD_AND_ENVIRONMENT.md) is still a placeholder: pick and record the
   revision before configuring, because changing it later is an ADR.
4. Fill the track ownership table in the research plan Part 7.3. An empty cell is a risk.
5. Prune the ECC surface per
   [`docs/ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md`](docs/ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md).

## Phase 2

Ordered so that each item has something already built to measure it.

1. **CI. Done, 2026-08-16.** [`.github/workflows/ci.yml`](.github/workflows/ci.yml) runs on
   every push and PR: `ruff check`, `ruff format --check`, `mypy`, `pytest` (which is the
   orientation assertion and the metric known-answer test, run as ordinary markers, not a
   separate job) and the organ manifest validator. Installs
   [`pipeline/requirements-ci.txt`](pipeline/requirements-ci.txt), which is the five packages
   the tree actually imports plus pytest, ruff and mypy — not the 109-package lock, because
   `docs/16` requires the commit set stay fast and because the lock's `torch==2.8.0+cpu` is a
   CPU-index local version that plain PyPI cannot resolve. `test_ci_requirements_match_lock.py`
   holds the two files at the same versions so a green gate is green against what the pipeline
   environment runs. Not yet in the gate, because nothing exists to run: the PHI-in-logs
   assertion (item 5 below) and the UI bundle lint (`docs/09`). The PR- and nightly-level gates
   in [`docs/16`](docs/16-TESTING_STRATEGY.md#ci) need a built application and stay out of
   scope until one exists.
2. **Linters and formatters. Done, 2026-08-16.** [`docs/14`](docs/14-CODING_STANDARDS.md#python)
   requires PEP 8 enforced by a formatter and a linter, and type hints that are checked rather
   than decorative. `pyproject.toml` configures `ruff` (`E`, `F`, `I`, `UP`, `B`) as both
   linter and formatter, and `mypy` with `disallow_untyped_defs` over the four packages.
   `ruff==0.16.3` and `mypy==2.3.1` are pinned in `pipeline/requirements.txt`. Twelve pre-
   existing lint findings fixed: unsorted imports, two lines over the 100-column limit, a
   bare `zip()` without `strict=`, and two `class X(str, Enum)` moved to `StrEnum`. Nine files
   reformatted for the 100-column width. The `StrEnum` move is the only one that changes any
   output: `f"{Level.STUB}"` is now `"stub"` rather than `"Level.STUB"`, which is why ruff
   classifies `UP042` as an unsafe fix. Nothing formats either enum without `.value` today.
3. **Pipeline stage 3, reorientation and resampling.** `reorient()` already exists and is
   tested against 48 storage orders. Resampling is the missing half, and it is where marker
   voxel counts start to change.
4. **The results-table writers** for tables 4.1 to 4.6, and Bland-Altman for volume error.
   The metrics exist; the thing that turns a list of them into the exact table that goes in
   the thesis does not. Hand-transcribing numbers is how numbers drift.
5. **The PHI-in-logs assertion**, the third cross-cutting test in
   [`docs/16`](docs/16-TESTING_STRATEGY.md#pyramid). Needs a PHI-seeded synthetic study.

## Known traps carried forward

- Z-Anatomy mirrors left and right by sharing one mesh datablock. `transform_apply` aborts
  on multi-user data with only a warning. Call `make_single_user(obdata=True)` first. This
  has already cost time twice, on BrainTwin and again on EarTwin.
- Z-Anatomy has dural sinuses but no cerebral veins, and cranial nerves are clipped at the
  skull base. Declared limitation, not a defect to fix. It goes in the organ manifest's
  `known_gaps` and is surfaced in the UI.
- Several structures in Z-Anatomy exist only as label leader lines, not surfaces. EarTwin
  found this the hard way after a discovery document claimed otherwise. Inventory the
  geometry, never the description files.
- `MESA_VK_DEVICE_SELECT` falls back to the default device silently on an unmatched PCI id.
  A benchmark launched that way measures the integrated GPU while logging the discrete one.
- Absolute timings on Machine A are comparable only within one capture batch. Cross-batch
  drift around 1.8x has been observed with no identified cause. Headline numbers must come
  from a single attended sitting. **The development machine is Machine A**, so a build or a
  pipeline job running during a capture invalidates it.
- Fedora 44 ships CMake 4.3, GCC 16.1, Python 3.14 and both Qt 5 and Qt 6 on `PATH`. Each
  one breaks either the superbuild or the pipeline environment, and each surfaces as an
  error naming a dependency rather than the real cause. Table in
  [`docs/15-BUILD_AND_ENVIRONMENT.md`](docs/15-BUILD_AND_ENVIRONMENT.md).
- `antspyx` publishes no cp314 wheel. On the system interpreter pip silently falls back to
  the sdist and starts compiling ITK. The pipeline venv is pinned to Python 3.12.
