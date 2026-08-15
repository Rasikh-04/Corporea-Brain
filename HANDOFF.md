# HANDOFF

Rolling state file. Anyone, human or agent, must be able to resume cold from this page.
Overwrite it; do not append a history. History lives in git and in `docs/DECISIONS/`.

## Last updated

2026-08-15 — repository put under git; environment scripts and pipeline pins landed.
Still no application code.

## Where the project is

Pre-development, now with a working environment definition. The two planning documents
(research plan, build plan) are settled at version 1 and mirrored under
[`docs/research/`](docs/research/). The desktop application's own documentation set is
complete and indexed at [`docs/00-INDEX.md`](docs/00-INDEX.md). Nothing in `app/`, `eval/`
or `ui/` exists yet. Those directories are specified, not built.

What landed this session:

- The repository is a git repo for the first time (`main`, no commits yet, everything
  staged). [`.gitignore`](.gitignore) enforces rule 8 — imaging formats, model weights,
  atlas assets and audit logs are all excluded, verified with `git check-ignore`.
- [`pipeline/requirements.txt`](pipeline/requirements.txt) — direct dependencies, every pin
  exact and resolved against cp312 manylinux, not guessed. Three entries stay
  `PLACEHOLDER` because they are blocked on ADR-006 and ADR-007.
- [`scripts/setup-env.sh`](scripts/setup-env.sh) and
  [`scripts/check-env.sh`](scripts/check-env.sh) — idempotent setup and a verifier that
  reports the checks it cannot yet run rather than omitting them.
- [`docs/15-BUILD_AND_ENVIRONMENT.md`](docs/15-BUILD_AND_ENVIRONMENT.md) gained a Fedora 44
  toolchain table and six new rows in the build-failures table.

**Nothing has been installed yet.** `setup-env.sh` needs a terminal for sudo and has not
been run. `check-env.sh` currently reports 5 fail, 3 warn.

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

## Next session: scaffolding phase 1

**Scope: everything that does not need Slicer.** The superbuild is deferred on disk, and
that is fine, because the work rule 7 puts first does not depend on it. "Build the measuring
instrument before the thing it measures." All four items below are pure Python against the
`.venv`, and together they convert three of the seven SKIPs in `scripts/check-env.sh` into
real, running tests.

Build in this order. The order is the point.

1. **Directory skeleton** per the repo map in [`CLAUDE.md`](CLAUDE.md): `app/`, `organs/`,
   `pipeline/`, `eval/`, `bench/`, `ui/`, `scripts/`. Each gets a `README.md` stating what
   it holds and which document specifies it. Empty directories are not committed by git;
   the README is what makes the structure real.
2. **The synthetic asymmetric phantom, and the orientation assertion against it.**
   [`docs/06`](docs/06-IMAGING_PIPELINE.md), the orientation section, and
   [`docs/16`](docs/16-TESTING_STRATEGY.md). This is rule 5 and it is first for a reason: a
   left/right flip invalidates every downstream number and is invisible when it happens.
   nibabel and numpy only. Satisfies check-env step 4.
3. **The evaluation harness known-answer test.** Two synthetic masks, Dice computed by hand,
   asserted against the implementation. [`docs/10`](docs/10-EVALUATION_PROTOCOL.md). Add
   HD95 and ASSD alongside Dice from the start, because Dice alone is misleading on small
   lesions. The harness never imports the application — architectural seam 4. Satisfies
   check-env step 5.
4. **Organ manifest schema and validator.** [`docs/04`](docs/04-ORGAN_MODULE_SPEC.md). A
   manifest that fails validation is reported, never silently skipped. Write the brain
   manifest with `known_gaps` populated from the Z-Anatomy traps below. Satisfies check-env
   step 6.

Items 2 and 3 are the two whose failures are silent. Nothing built on top of a broken
orientation or a broken metric is worth anything.

**Not in this phase:** anything touching MRML, Qt or a Slicer module type, all of which need
the superbuild. Also nothing that hard-codes a parcellation, an atlas or a coordinate space,
because ADR-006 is still open and seam 5 forbids it. Where the atlas would be named, take a
configuration value and leave `<PARCELLATION>`.

## Immediate next actions

0. **Finish `scripts/setup-env.sh`.** Partly done: python3.12, dcm2niix and ccache are
   installed, and torch 2.8.0+cpu is in the venv. The requirements install is slow on this
   link and has failed once mid-download, reported as a missing package. Re-run it; pip
   resumes from cache. Confirm with `scripts/check-env.sh` and commit
   `pipeline/requirements.lock.txt`.
1. Slicer superbuild, **deferred on disk and not blocking phase 1**. ~40 GB free against a
   60 GB minimum, and `~/Projects` is 18 GB of largely stale archives. When disk is freed,
   gate with `scripts/check-env.sh --superbuild` before configuring. Note that
   `<PINNED_REVISION>` in [`docs/15`](docs/15-BUILD_AND_ENVIRONMENT.md) is still a
   placeholder: pick and record the revision before configuring, because changing it later
   is an ADR.
2. Run the orientation exercise: one DICOM study, convert, verify left is left in three
   independent tools, write down the verification method. It becomes a CI test.
3. Fill the track ownership table in the research plan Part 7.3. An empty cell is a risk.
4. Close ADR-006. Nothing in the pipeline can be written correctly before it.
5. Prune the ECC surface per
   [`docs/ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md`](docs/ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md).

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
