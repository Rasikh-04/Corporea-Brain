# HANDOFF

Rolling state file. Anyone, human or agent, must be able to resume cold from this page.
Overwrite it; do not append a history. History lives in git and in `docs/DECISIONS/`.

## Last updated

2026-10-12 — **Demonstration material for the instructor meeting added under [`demo/`](demo/).**
No decision changed and no application code was written. `demo/run-demo.sh` steps through
eleven labelled stages (platform, ours, mock) against the built Slicer and three public Slicer
sample scans fetched into git-ignored `build/demo-data/`; `demo/briefing.html` is the page
shown beside it. A full rehearsal ran green. The GUI was launched for the first time, which
closes the "launch the GUI once" follow-up below, and it surfaced **two defects of this build
(5.12.3 against system Qt 6)**: opening the Volume Rendering module panel closes the
application, and the Segment Editor Smoothing effect raises a `TypeError` when its panel
updates. Volume rendering itself works through the module logic. Neither is fixed; both will
matter to the application layer and are not yet in `docs/15`. The meeting may close or move
ADR-003's standing with the instructor and ADR-004 to ADR-007; record the outcome here.

2026-08-17 — **The build phase is closed.** Every gate was re-run from the repository root at
close and all are green: 271 tests in 2.5 s, `ruff check`, `ruff format --check`, `mypy` over
14 files, and the organ manifest validator. All four marked assertion classes pass on their own
(orientation 85, PHI 21, seam 6, known-answer 24). One gate defect was found and fixed in the
process, described under "Closing the build phase" below. Nothing is blocking; the next phase
is the application layer, gated on ADR-006.

2026-08-17 — **The Slicer superbuild completed for the first time on Machine A.**
`Slicer 5.12.3-2026-07-22` builds and runs, matching the pin in
[ADR-010](docs/DECISIONS/ADR-010-slicer-pinned-revision.md). **146 modules load: 51 CLI, 27
loadable, 68 scripted**, counted by asking the running application, not by counting files.
The finished tree is 6.9 GB and 57 GB remains free, so the disk blocker that dominated this
file is **retired**. The application layer is no longer blocked.

Those module counts correct the ones in commit `cf79551`, which read 101 CLI and 174 loadable.
Both were file counts in the output directories rather than module counts: `cli-modules/` holds
51 descriptors beside 50 executables for the same 51 modules, and `qt-loadable-modules/` holds
175 files of which most are support libraries. The check is
`slicer.app.moduleManager()`, classifying each loaded module by `className()`, and it
self-checks because the three categories sum to the reported total. Counting build output as
though it were modules is the same mistake docs/15 already warns about for the completion
marker: prefer the artifact that answers the question over the one that is easy to count.

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

## Closing the build phase

Two things were wrong at close and both are fixed. Neither was caught by CI, which is the
point worth carrying forward: **both hid in the gap between what CI runs and what a person
runs.**

**The module counts were file counts.** Recorded above. CI could never have caught this because
CI does not have a built Slicer.

**`ruff format` was rewriting documentation.** CI runs `ruff format --check pipeline eval app
scripts`, four explicit directories, and is green. But `pyproject.toml` excluded only `build`,
so the bare `ruff format .` that any developer or agent would naturally run at the repo root
reached into `docs/` and reformatted the Python blocks inside our markdown. Those blocks are
illustrative fragments, not modules, and the formatter's output for them is not merely noisy,
it is wrong: it rewrites the dict literal in
[`docs/ai-workflow/A1`](docs/ai-workflow/A1-MODEL_ROUTING_AND_COST.md) into a tuple, silently
corrupting a documented example. `extend-exclude` now lists `build`, `docs`, `organs`, `Slicer`
and `Slicer-build`, so the configuration enforces the scope its own header already claimed.
Root and CI-scoped runs now agree, which is the property that was actually missing.

The general lesson for the phases after this one: a gate that passes in CI and fails, or
silently damages something, when run by hand is not a gate. Where CI narrows its scope with an
explicit path list, the configuration has to narrow the same way, or the two drift and only the
human ever sees the difference.

## Next phase: the vertical slice

The next phase is **Phase 3, weeks 13 to 22, one disorder end to end and measured**, which is
the **R2** rung and the thesis artifact. Ischemic stroke first. Defined in
[the research plan](docs/research/FYP_Brain_Digital_Twin_Reasoning_and_Research_Plan.md#phase-3);
the strict order of work is set there and should not be reordered casually.

**The gate out of it is numeric, not visual:** real numbers in a table for segmentation
(Dice, HD95, ASSD) and for region attribution agreement. Not screenshots.

What is already in place for it, which is most of the hard part of rule 7:

- The evaluation harness and all six results tables exist and are tested, so **the measuring
  instrument is built before the thing it measures.** Numbers have somewhere to land on day one.
- The orientation assertion exists and runs on every commit, so stage 3 onward cannot silently
  invert laterality.
- The PHI assertion exists and is written so later stages join one test rather than adding one.
- A working Slicer to host the application layer.

What is genuinely not in place, in the order it will bite:

1. **ADR-006 is open and it is the top blocker.** Canonical coordinate space and parcellation
   atlas. Stages 7, 8 and 10 (template registration, parcellation, region attribution) are
   exactly steps 3 and 4 of the phase gate, and none of them can be written before it closes.
   Every deferred check in `validate_organs.py` points at it and the brain manifest still
   carries the `<PARCELLATION>` placeholder. **Close this first. Nothing else competes.**
2. **No datasets and no downloaders.** `scripts/README.md` says so directly. Phase 3 needs
   ATLAS for stroke masks. Rule 8 means downloader scripts only, never the data, and the DUA
   has to be in hand before the download, not after.
3. **Twelve of thirteen pipeline stages do not exist.** Only stage 3 is built.
   [`docs/06`](docs/06-IMAGING_PIPELINE.md) specifies stages 0 to 12; the phase needs 0, 1 and
   2 before stage 3 has real input, then 4 through 10 to reach the gate.
4. **ADR-007 is open and due before R2.** Record store technology, which the clinical record
   and timeline in steps 6 and 7 sit on.
5. The two build-tree-only Fedora fixes are still unreproducible from the repository.

The honest read: the scaffolding phase is finished and finished well, but **the next phase
cannot start on its real work until ADR-006 closes.** The one thing that can proceed in
parallel is dataset access, because the paperwork is the long pole and it does not depend on
any decision here.

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
   Verified again on 2026-08-17 at phase close, from the artifacts rather than from any
   completion marker: the launcher starts, the embedded Python runs, the application reports
   `5.12.3-2026-07-22` at revision `34627`, and 146 modules load as 51 CLI, 27 loadable and 68
   scripted. That was a headless run (`--no-main-window --exit-after-startup`), which is what
   makes it usable as a check later. **Launching the GUI once and recording what the main
   window shows is still open**, and is a human step, not an automated one.

   The other open follow-up is to decide whether the two build-tree-only fixes get pre-empted
   in the configure step so a clean rebuild does not rediscover them. This is the largest
   unbounded risk left in the build: the fixes exist only in `Slicer-build/`, nothing in the
   repository reproduces them, and the machine that rebuilds next pays the same two days.
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

## Disk, and why the workspace partition does not solve it (history, superseded)

**This section is no longer live and nothing here blocks anything.** It is kept because the
reasoning is worth having on record, not because the numbers still hold. The superbuild
finished in 6.9 GB, `/` now has **57 GB free**, and the 60 GB minimum it argues against was a
planning figure for an unknown machine rather than a measurement of this one. Read it as an
account of how the budget was reasoned about while the size was unknown. The one item in it
that is still actionable is `link-workspace.sh`, which has still not been run and no longer
needs to be: `/mnt/workspace` is not currently mounted and `build/` is an ordinary directory.

Measured 2026-08-16, when the numbers below were current. Table and the three routes to 60 GB
are in [`docs/15`](docs/15-BUILD_AND_ENVIRONMENT.md#disk-routes).

At that time `/` had **46 GB free** against a 60 GB superbuild minimum. The `workspace` partition
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
