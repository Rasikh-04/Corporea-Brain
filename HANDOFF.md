# HANDOFF

Rolling state file. Anyone, human or agent, must be able to resume cold from this page.
Overwrite it; do not append a history. History lives in git and in `docs/DECISIONS/`.

## Last updated

2026-08-17 — **The Slicer superbuild completed for the first time on Machine A.**
`Slicer 5.12.3-2026-07-22` builds and runs, matching the pin in
[ADR-010](docs/DECISIONS/ADR-010-slicer-pinned-revision.md). 101 CLI modules, 174 loadable
modules, 68 scripted modules; the finished tree is 6.9 GB and 57 GB remains free, so the disk
blocker that dominated this file is **retired**. The application layer is no longer blocked.

Getting there cost two upstream defects, both specific to a distro newer than Slicer 5.12.3
expects, and both now recorded in [`docs/15`](docs/15-BUILD_AND_ENVIRONMENT.md): PythonQt
wrapper generation under Qt 6, and static curl silently linking Fedora's libidn2. **Both fixes
live in the build tree only and do not survive a clean rebuild.** Read those two sections
before rebuilding anywhere.

2026-08-16 — **Phase 2 is closed.** All five items are done: CI, linters, pipeline stage 3,
the results-table writers with Bland-Altman, and the PHI-in-logs assertion. 271 tests pass in
under three seconds; ruff, mypy and the organ manifest validator are green. Three of the four
cross-cutting assertions in `docs/16` now run on every commit; the fourth, the UI bundle lint,
waits on a UI bundle existing. Still no application code, and that is on plan.

## Where the project is

The measuring instruments are built and the thing they measure is not, which is the ordering
rule 7 demands. 271 tests pass in under three seconds against `pytest.ini`.

The two planning documents are settled at version 1 and mirrored under
[`docs/research/`](docs/research/). The document set is complete and indexed at
[`docs/00-INDEX.md`](docs/00-INDEX.md).

What landed in phase 1, in the order it was built:

1. **Directory skeleton.** `app/`, `organs/`, `pipeline/`, `eval/`, `bench/`, `ui/`,
   `hardware/`, `scripts/`, each with a `README.md` naming what it holds and which document
   specifies it.
2. **The orientation assertion.** [`pipeline/corporea_pipeline/orientation.py`](pipeline/corporea_pipeline/orientation.py)
   and [`phantom.py`](pipeline/corporea_pipeline/phantom.py). The one idea it encodes: **the
   assertion is made in world space, never in voxel space.** A test proves why, by showing
   that a correct reorientation to LAS and a broken flip along i produce *byte-identical
   arrays* and differ only in the affine. Any voxel-index check fails the safe operation and
   passes the fatal one. The phantom is checked against all 48 possible storage orders, and
   against a deliberately broken fixture per axis.
3. **The evaluation harness.** [`eval/corporea_eval/metrics.py`](eval/corporea_eval/metrics.py):
   Dice, HD95, ASSD, volume error, distances in millimetres. Every expected value in
   `test_metrics_known_answer.py` was computed by hand and the arithmetic is in the docstring.
   No metric returns a bare float; each carries a degeneracy flag, and
   [`aggregate.py`](eval/corporea_eval/aggregate.py) refuses to average over undefined values
   without being told which policy applies.
4. **The organ manifest schema and validator.** [`app/corporea_core/organ_manifest.py`](app/corporea_core/organ_manifest.py),
   run by [`scripts/validate_organs.py`](scripts/validate_organs.py). Collects every issue with
   a dotted field path rather than stopping at the first. Four of the seven checks in docs/04
   run; three are reported `DEFERRED` with the reason, never omitted.

Three architectural seams are now asserted mechanically rather than by review: seam 4 (the
harness never imports the application), the no-Slicer-imports rule for `corporea_core`, and
seam 5 (the brain manifest carries `<PARCELLATION>`, not an atlas name).

`scripts/check-env.sh` steps 4, 5 and 6 now run the real tests instead of printing SKIP.

**The environment is green.** `scripts/setup-env.sh` finished, and `scripts/check-env.sh`
reports **0 fail, 3 warn** in `.venv`, with steps 4, 5 and 6 passing there.
`pipeline/requirements.lock.txt` is committed: 109 packages, exact.

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
3. Slicer superbuild, **done**. It built and runs; the revision is pinned in
   [ADR-010](docs/DECISIONS/ADR-010-slicer-pinned-revision.md) and the two Fedora 44 traps are
   written up in [`docs/15`](docs/15-BUILD_AND_ENVIRONMENT.md#superbuild). The disk section
   below is kept as the record of how the budget was reasoned about, but it is now history:
   the finished tree measures **6.9 GB**, roughly a ninth of the 60 GB planning figure,
   because this build is Release against system Qt with ccache. That is the finished size,
   not the peak, and it holds for this configuration only.
   The open follow-ups are to launch the application once and record what it shows, and to
   decide whether the two build-tree-only fixes get pre-empted in the configure step so a
   clean rebuild does not rediscover them.
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
3. **Pipeline stage 3, reorientation and resampling. Done, 2026-08-16.**
   [`pipeline/corporea_pipeline/resample.py`](pipeline/corporea_pipeline/resample.py). The
   output affine is built first, from the input direction cosines and the requested spacing,
   and the sampling grid is then derived *from that affine* by mapping every output voxel back
   through world space. There is deliberately no second place where the array and the affine
   could be made to disagree. `run_stage3` reorients, resamples, and refuses to return a volume
   whose geometry moved.

   Three things were learned building it, and each changed the code.

   - **The determinant-sign check belongs to the resample, not to the stage.** The first
     version asserted the sign across the whole stage and failed on every correct run: `RAS` is
     right-handed and `LAS` is left-handed, so rewriting one as the other legitimately flips
     it. That is what stage 3 is *for*. The resample only rescales, so across it the sign is
     invariant, and that is where the assertion now sits.
   - **The world bounding box check does not catch a flip.** It catches an affine that was not
     updated to match a grid that was, which is the classic dropped-affine resample. Data
     flipped *with* its affine left intact moves no world coordinate the shape can see. Only a
     marker finds that, which is the whole argument for the phantom.
   - **Linear interpolation on a label volume is not caught by anything downstream.** The
     expectation was that it would fail the orientation assertion. It does not: the blur erodes
     a marker symmetrically, so its centre of mass stays put and laterality survives. What
     actually happens is that it invents 121 intensity values that are not any label, and
     erodes every marker by roughly a third, in a volume that passes every geometry check in
     the repository. Hence `Interpolation` is a required argument with no default: the guard
     has to be at the call site because there is no downstream guard.

4. **The results-table writers. Done, 2026-08-16.**
   [`eval/corporea_eval/tables.py`](eval/corporea_eval/tables.py) and
   [`bland_altman.py`](eval/corporea_eval/bland_altman.py). All six tables from `docs/10` are
   declared as data and rendered as markdown with a required version stamp.
   `test_tables.py::test_every_table_matches_the_protocol_document` parses `docs/10` and
   asserts every column header and row label is identical, so neither the document nor the code
   can be redesigned without the other failing the gate.

   Declared rows always print, as `pending` rather than as an absent line: rule 4 applies to
   results tables most of all, because the size band the segmenter could not handle is exactly
   the row a "skip empty rows" renderer would drop.

   Bland-Altman reports bias, the 95% limits of agreement, and the correlation between the
   differences and the case means, which is the standard proportional-bias check and the first
   thing an examiner asks about. Cohorts under three cases are refused rather than degraded:
   there is no honest table cell for limits of agreement over two cases. `BOTH_EMPTY` cases are
   excluded and counted; every other degeneracy stays in, because dropping the total misses
   would be the single most flattering thing the module could do.

   One document change: `docs/10` specified tables 4.5 and 4.6 in prose rather than as tables,
   so the drift test could only have covered four of six. They are now written out with
   explicit columns, consistent with what the prose said.

5. **The PHI-in-logs assertion. Done, 2026-08-16.**
   [`pipeline/corporea_pipeline/phi.py`](pipeline/corporea_pipeline/phi.py), with a synthetic
   study seeded in every field `docs/12` names as identified. It runs against the pipeline
   output that exists — stage 3, its log at DEBUG, and its provenance record — and is written
   so later stages join one test rather than needing a new one.

   The design point: **an exact substring scan gives confident, wrong assurance.** PHI reaches
   a log reformatted. A date seeded as `1974-03-02` arrives as `02/03/1974` or `19740302`; a
   phone number arrives with different separators; a name arrives as the surname alone in an
   export path. So each field expands into the forms it is plausibly written in, and numbers
   are compared digit-only.

   Two things that were wrong on the first pass and are worth remembering:

   - **`\b` is the wrong anchor for a name.** `_` is a word character to `\b`, so a scanner
     anchored on it finds no boundary in `SURNAME_19740302` and reports the directory as clean.
     That is the single most common shape a leaked name arrives in, DICOM export trees being
     named that way almost by convention. The guard now treats only letters and digits as word
     characters, and drops entirely at an edge that is not alphanumeric, which `\b` also got
     wrong for any needle starting with `/`.
   - **Digit matching must be per run, not per document.** Stripping every non-digit from the
     whole text welds unrelated numbers together, so `case 1974 step 0302` would report a date
     of birth that is not there. A false positive here is not harmless: it is the kind of
     finding that gets the check disabled.

   Findings name the field and the form and never the value. The failure message goes into the
   CI log of the run that caught the leak, and a PHI scanner whose own output is PHI has solved
   nothing.

## Disk, and why the workspace partition does not solve it

Measured 2026-08-16. Table and the three routes to 60 GB are in
[`docs/15`](docs/15-BUILD_AND_ENVIRONMENT.md#disk-routes).

`/` has **46 GB free** against a 60 GB superbuild minimum. The `workspace` partition
(`/dev/nvme0n1p6`) is **19.4 GB in total, 18 GB free**. Linking it into the repository does not
close the gap and cannot: a symlink relocates a directory, it does not pool free space across
filesystems. A build that lands there gets 18 GB.

Two things changed so this is not re-litigated from an estimate next time.

- [`scripts/link-workspace.sh`](scripts/link-workspace.sh) points `build/` at the workspace
  partition. Worth doing — scratch volumes, the generated phantom and ccache grow without
  bound and currently grow on the filesystem the superbuild has to fit into — but it buys
  headroom on `/`, it does not replace it. Needs `sudo`, because `/mnt/workspace` is
  root-owned. It has not been run.
- `check-env.sh` now measures the filesystem that holds `build/`, not the repository root, and
  names it in the verdict. Before this change, symlinking `build/` onto a small partition would
  have produced a *more* optimistic number, which is the wrong direction for a check whose
  failure mode is a superbuild dying partway with an error that does not mention disk.

The recommended route is to free 14 GB on `/`: `~/.config` is 17 GB and `~/Projects` is 11 GB
on a machine whose active project is 2 GB of it. The durable answer is to shrink the 72.8 GB
NTFS `Data` partition and grow `workspace` into it, which needs gparted, a backup and an
offline session.

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
