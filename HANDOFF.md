# HANDOFF

Rolling state file. Anyone, human or agent, must be able to resume cold from this page.
Overwrite it; do not append a history. History lives in git and in `docs/DECISIONS/`.

## Last updated

2026-08-16 — first three commits on `main`. Phase 1 scaffolding is complete: the orientation
assertion, the evaluation harness and the organ manifest validator all exist and pass. Still
no application code, and that is on plan.

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

**The environment is still installing.** `scripts/setup-env.sh` has been running since 20:28
and pip is still downloading; `check-env.sh` reports 9 fail, 4 warn against an incomplete venv.
The phase 1 code above was verified in a throwaway venv, not in `.venv`. **Re-run
`scripts/check-env.sh` once the install finishes** and confirm 4, 5 and 6 go green there too.

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

## One deviation from the documents, recorded here rather than buried

[`docs/06`](docs/06-IMAGING_PIPELINE.md) says the phantom is "committed to the repository."
It is not. It is a deterministic generator, written out on demand by
[`scripts/make_phantom.py`](scripts/make_phantom.py) into git-ignored `build/`. The reasoning
is in the `phantom.py` module docstring; the short version is that `.gitignore` blocks every
imaging extension under every path on purpose, and punching an exception through `*.nii.gz`
for a fixture is precisely the gap its own header warns about. A generator is also auditable
where a binary is not, and cannot go stale.

**If this is wrong, say so and it changes.** Otherwise amend docs/06 to match. Leaving the
document and the code disagreeing is the worse of the three options.

## Immediate next actions

0. **Finish `scripts/setup-env.sh`.** Still running as of this handoff. python3.12, dcm2niix
   and ccache are installed and torch 2.8.0+cpu is in the venv; the requirements download is
   slow on this link and has failed once mid-download, reported as a missing package. If it
   fails again, re-run it; pip resumes from cache. Then run `scripts/check-env.sh` and
   confirm steps 4, 5 and 6 pass in `.venv`, and commit `pipeline/requirements.lock.txt`.
   Note `PyYAML==6.0.3` was added to `pipeline/requirements.txt` **after** this install
   started, so it will need a second `pip install -r`.
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
3. Slicer superbuild, **still deferred on disk and still not blocking**. ~40 GB free against
   a 60 GB minimum, and `~/Projects` is 18 GB of largely stale archives. When disk is freed,
   gate with `scripts/check-env.sh --superbuild` before configuring. `<PINNED_REVISION>` in
   [`docs/15`](docs/15-BUILD_AND_ENVIRONMENT.md) is still a placeholder: pick and record the
   revision before configuring, because changing it later is an ADR.
4. Fill the track ownership table in the research plan Part 7.3. An empty cell is a risk.
5. Prune the ECC surface per
   [`docs/ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md`](docs/ai-workflow/A2-CONTEXT_BUDGET_AND_SESSION_HYGIENE.md).

## Phase 2, when the environment is green

Ordered so that each item has something already built to measure it.

1. **CI.** Everything above runs in about two seconds and none of it runs automatically. The
   commit-level gate in [`docs/16`](docs/16-TESTING_STRATEGY.md#ci) is the orientation
   assertion, the metric known-answer test, the manifest validator and the linters. Wire it
   before the test count grows enough that a red run is normal.
2. **Linters and formatters.** [`docs/14`](docs/14-CODING_STANDARDS.md#python) requires PEP 8
   enforced by a formatter and a linter in CI, and type hints that are checked rather than
   decorative. None of that is configured yet.
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
