# Parallelism, Benchmarking and Local-Automation Policy
### BrainTwin — Qt/C++/VTK on 3D Slicer (FYP)

Sources read (all files, in full):

**ECC skills**
- `/home/rasikh/.config/Claude/local-agent-mode-sessions/89f22721-d9c7-45be-a6f0-38f9f24a9f64/3596fda3-1821-496a-bed7-7675f3843c79/rpm/plugin_016jTqahv5nuHriZfVWTLkrG/skills/parallel-execution-optimizer/SKILL.md`
- `.../skills/benchmark-optimization-loop/SKILL.md`
- `.../skills/autonomous-agent-harness/SKILL.md`
- `.../skills/benchmark/SKILL.md`
- `.../skills/agent-eval/SKILL.md`

(each skill directory contains exactly one file, `SKILL.md`; there are no `reference/` or `scripts/` subdirectories)

**Project**
- `/home/rasikh/Projects/BrainTwin_Native/docs/01-scope-and-methodology.md`
- `/home/rasikh/Projects/BrainTwin_Native/docs/03-metrics-and-test-matrix.md`
- `/home/rasikh/Projects/BrainTwin_Native/stacks/TIER0_CONTRACT.md`
- `/home/rasikh/Projects/BrainTwin_Native/stacks/TIER1_CONTRACT.md`
- `/home/rasikh/Projects/BrainTwin_Native/harness/{run_tier0.sh,run_tier1.sh,run_matrix.sh,footprint.sh,check_env.sh,gpu_select.sh,results.py,report.py,import_results.py}`
- `/home/rasikh/Projects/BrainTwin_Native/results/runs.csv` (header + rows; 177 data rows)

**Measured state of the existing harness** (from `runs.csv`, not assumed):
Tier 0 is complete — Qt+C++ 40 rows, Rust+wgpu 40, Avalonia 40. Tier 1 is not — Rust+wgpu 56 rows, Qt+VTK **1 row**, Avalonia **0**. The stack decision (Qt) was made without a completed Tier 1 matrix. This policy treats that as settled and repoints the harness at application NFRs; it does not propose finishing Tier 1.

---

## 1. Fan-out decision rule

### 1.1 The four criteria

A task fans out into sub-agents only if it passes **all four gates**. Failing any one gate means inline.

| Gate | Test | Fails when |
|---|---|---|
| **G1 Independence** | Write surfaces of the proposed lanes are provably disjoint — different files, different build dirs, different worktrees, different CSV batches. Reads may overlap freely. | Two lanes would both edit `CMakeLists.txt`, both append to `results/runs.csv`, both configure the same build tree, or both need the GPU/compositor. |
| **G2 Breadth** | ≥3 independent lanes, **or** the search space is "unknown location across >20 files". Below that, an agent's cold-start context re-derivation costs more than it saves. | 1–2 lanes, or the file is already known. |
| **G3 Cost of a wrong answer** | Wrong answer is caught by a deterministic gate you already own (compile, ctest, `report.py --check`, `gpu_select.sh verify`). | The output is a judgement call with no mechanical check — e.g. "is this clinically sensible", "which architecture". A sub-agent's confident wrong answer arrives without its evidence and is expensive to audit. Do it inline where you see the reasoning. |
| **G4 Context cost** | Expected raw output ≫ expected conclusion. A lane that would dump 3k lines of `ldd`/CMake log to return one sentence is a good lane. | The parent needs the raw material anyway (e.g. it must edit the files it is reading). Fanning out then forces a second read. |

Two hard overrides, both from `parallel-execution-optimizer`:

- **Never parallelise measurement.** Any lane that touches the GPU, the compositor, the CPU governor, or appends to `runs.csv` runs **strictly serial**, one at a time. `TIER0_CONTRACT.md` documents a ~1.8× cross-batch drift on all three stacks simultaneously from unidentified machine state; two concurrent lanes contending for the same GPU would manufacture exactly that noise, inside a single batch, where the harness's own batch rule can no longer catch it.
- **Never parallelise destructive or migration-shaped work.** Schema changes to `results.py:COLUMNS`, `runs.csv` rewrites, Slicer superbuild reconfigures.

### 1.2 This project's recurring tasks

| Task | Verdict | Why |
|---|---|---|
| Locate where a Slicer module registers a widget / find an unfamiliar VTK or MRML API's usage in the Slicer tree | **FAN-OUT** (`Explore`, 1–3 lanes) | G1 read-only, G2 the Slicer source tree is huge, G4 huge output → one path. |
| Fix a C++ build error in our module | **INLINE** | G2 fails — the error names the file. G4 fails — you must edit what you read. |
| Full Slicer superbuild from clean | **INLINE**, single lane, background | G1 fails against anything else touching the build tree. Serial by nature. `-j$(nproc)` is the parallelism here, not agents. |
| Cross-cutting review of one PR (memory safety / VTK pipeline correctness / Qt threading / clinical-data handling) | **FAN-OUT** (3–4 reviewer lanes, read-only) | G1 read-only, G2 four distinct lenses, G3 each finding cites a file:line you can check, G4 yes. |
| Implement one NFR fix (e.g. reduce ingest wall time) | **INLINE** | G3 fails — the correctness bar is the benchmark itself, and only one agent can hold the GPU. |
| Benchmark variant sweep (step size, texture format, threading) | **INLINE orchestration, serial execution** | Variants are *generated* in parallel, *measured* one at a time. See §3.4. |
| Dependency + licence audit across Slicer, VTK, ITK, Qt, our third-party | **FAN-OUT** (2–3 lanes by dependency family) | G1 read-only, G2 hundreds of packages, G4 yes. |
| Write/refresh a doc section from code | **INLINE** | G3 fails — no mechanical check on prose. |
| Sweep the repo for a rename (`Get*` → `get*`, header path change) | **INLINE** | G1 fails outright — one shared write surface. |
| Reproduce a defect on a fixed case set | **FAN-OUT only if each case gets its own worktree + its own Slicer settings dir** | Otherwise G1 fails on `~/.config/slicer.org/`. See §2. |
| Triage a failed nightly job | **INLINE** | G2 fails — the log says where. |

### 1.3 Measurement that validates the rule

The rule is a hypothesis. Measure it, per `benchmark-optimization-loop`'s ledger requirement.

Append one row per delegation decision to `/home/rasikh/Projects/BrainTwin_Native/results/agent_runs.csv`:

```
date, task_id, task_class, mode, lanes, wall_clock_s,
input_tokens, output_tokens, usd_est,
rework, gates_passed, notes
```

- `mode` ∈ `inline` | `fanout`
- `task_class` = the row label from §1.2
- `rework` ∈ `none` | `minor` | `redone` — did the parent have to re-read what a lane summarised, or redo the work?
- `gates_passed` = e.g. `G1G2G4` for an inline decision that failed G3

**Validation, after 20 decisions minimum, ≥3 per task class:**

The rule is **kept** for a task class when fan-out on that class shows median wall-clock ≥1.5× faster than inline *and* `rework != none` in ≤20% of runs. It is **reverted to INLINE** for that class when either condition fails. Cost is reported alongside but is not the gate — a 2× speedup at 3× tokens is a legitimate trade for a deadline, and the ledger should let the team make that call explicitly rather than by feel.

The honest control problem: you rarely run the same task both ways. Two mitigations, use whichever fits — (a) for the *first* three instances of each class, deliberately alternate mode; (b) accept that `rework` is the more reliable signal than wall clock, because it needs no counterfactual.

---

## 2. Worktree isolation for a CMake/Slicer superbuild

`agent-eval`'s worktree-per-run isolation is the right primitive, but a Slicer superbuild breaks the naive version of it: git worktrees isolate *source*, and almost everything that collides here lives outside the source tree.

### 2.1 Where parallel agents actually collide

| Collision | What happens |
|---|---|
| **In-source or fixed-path build dir** (`build/`, `Slicer-build/`) | Two worktrees configured to the same `-B` clobber each other's objects. Silent: you get a linked binary from mixed trees. |
| **`CMakeCache.txt` absolute paths** | The cache pins `CMAKE_SOURCE_DIR`, `Slicer_DIR`, `VTK_DIR`, `Qt6_DIR` as absolute. Copying or reusing a build dir across worktrees produces a build of *the other worktree's* sources with no warning. A cache never travels. |
| **ExternalProject stamp/download/tmp dirs** | The superbuild's `*-stamp/` files are the only record that VTK/ITK/CTK/python were built. Two jobs sharing a stamp dir → one sees another's `*-build` stamp and skips a build it needed. Downloads race on the same tarball. |
| **Generated headers** | `*Export.h`, `vtk*Module.h`, AUTOMOC `moc_*.cpp` / `*_autogen/`, AUTOUIC `ui_*.h`, and Slicer's Python-wrapping generated sources are written into the build tree. Shared build tree = one agent's stale generated header compiled against another's changed class. Manifests as a link error naming a symbol nobody wrote. |
| **`~/.config/slicer.org/Slicer.ini`, `~/.slicer.org/`** | Per-*user*, not per-checkout. Extension paths, module search paths, last-opened scene, "additional module paths" all live here. Two Slicer instances started concurrently by two agents interleave writes; one wins the file. This is the single most likely cause of "it worked when I ran it alone". |
| **Slicer's built-in Python/web server port, `--python-script` temp files** | Fixed default port → second instance fails or attaches to the first. |
| **ccache / `~/.cache/`** | Shared cache is *safe* and desirable (it is content-addressed), but `ccache -M` eviction under two full superbuilds will thrash. Raise the limit, don't isolate it. |
| **GPU, compositor, and the 60 Hz panel** | Not shareable at all for anything measured. |
| **`results/runs.csv`** | Two appenders → interleaved rows, no locking in `results.append_run`. Also destroys the batch semantics `report.py` relies on. |

### 2.2 The isolation contract

For each parallel implementation lane, all of the following, or the lane is not isolated:

```bash
LANE=lane-$N
git worktree add /home/rasikh/Projects/BrainTwin_App.worktrees/$LANE <branch>

# 1. Build tree OUTSIDE the worktree, named after the lane. Never in-source.
export BT_BUILD=/home/rasikh/.cache/braintwin-builds/$LANE
cmake -S /home/rasikh/Projects/BrainTwin_App.worktrees/$LANE -B $BT_BUILD ...

# 2. Superbuild externals get their own prefix per lane, or are pinned to ONE
#    shared read-only prefix built once up front (preferred — see below).
#    Never a shared writable prefix.
-DSlicer_DIR=/opt/slicer-superbuild-readonly/Slicer-build

# 3. Slicer runtime state per lane.
export XDG_CONFIG_HOME=$BT_BUILD/xdg-config
export XDG_CACHE_HOME=$BT_BUILD/xdg-cache
#    (Slicer also honours --settings-path / --no-splash / --testing)

# 4. Shared ccache, raised limit, NOT isolated.
export CCACHE_DIR=/home/rasikh/.cache/ccache   # ccache -M 40G

# 5. Nothing in this lane appends to results/runs.csv.
```

**Strongest single recommendation: build the Slicer superbuild once, keep it read-only, and give every lane `-DSlicer_DIR=` pointing at it.** Our module is an extension/loadable module against a stable Slicer — rebuilding VTK+ITK+CTK+Qt per lane costs an hour each and buys nothing. Parallel lanes then build only our own module (minutes), and the superbuild becomes a deliberate, serial, infrequent operation. This collapses collisions 1–4 to just the per-lane module build dir.

Cleanup rule: a lane's worktree and its `$BT_BUILD` are deleted together, or neither. An orphaned build dir with a stale `CMakeCache.txt` pointing at a deleted worktree is the classic "CMake Error: could not find source directory" that costs an afternoon.

---

## 3. Repurposing the harness as the ongoing NFR benchmark

The harness was built to answer "which stack". That question is closed. Its actual value is the discipline encoded in it — one writer, one reader, batch-scoped comparison, status-not-deletion, verified GPU binding — which is worth more than the stack numbers ever were. Keep the machinery, change the axis.

### 3.1 Axis change: `stack` → `variant`

Reinterpret, do not rename (renaming invalidates 177 existing rows and every session write-up):

| Column | Old meaning | New meaning |
|---|---|---|
| `stack` | Qt+VTK / Rust+wgpu / Avalonia | `BrainTwin@<short-sha>` — the build under test. Historical rows keep their old values and are distinguishable by `tier`. |
| `tier` | 0 = hello world, 1 = volume viewer | Add `2` = application NFR. Tier 0/1 rows become the historical baseline, never re-run. |
| `render_technique` | idiomatic path per stack | the app's render config (mapper, texture format, sample distance) — still the "what is not pinned" column. |
| `batch_id` | one sitting, licenses cross-stack comparison | **unchanged and load-bearing**: now licenses baseline-vs-HEAD comparison. See §3.4. |
| `pass_fail` | Tier 1 60 fps gate | per-NFR gate verdict. |
| `status` / `status_reason` | valid/superseded/invalid | unchanged. |

### 3.2 Metrics that carry over unchanged

- `cold_start_s` / `first_frame_s` — the `BRAINTWIN_FIRST_FRAME_MONOTONIC_NS` stdout marker from `TIER0_CONTRACT.md` transplants directly into the Slicer app's first-paint path. Keep the "emit after paint work, first paint only, CLOCK_MONOTONIC, flush" rules verbatim.
- `fps_avg`, `frame_time_p95_ms`, `frame_time_p99_ms` — MangoHud, same config, same `log_duration=29` quirk (covers script seconds 1–30, excluding warm-up), same "HUD is drawn during every capture" caveat.
- `peak_ram_mb`, `peak_vram_mb`, `installed_size_mb` — `footprint.sh`. **Use `dir` mode, not `elf`.** A Slicer app is a self-contained tree with its own Qt/VTK/ITK/Python; `elf` on the launcher would understate it by orders of magnitude — the exact failure `footprint.sh` already documents for the Avalonia apphost (~70 KB reported against a 98 MB publish).
- `compile_cold_s` / `compile_warm_s` — hyperfine, but redefine: cold = our module from clean against the prebuilt superbuild, **not** a full superbuild. Record the superbuild time separately and once, as prose, not as a row.
- `governor`, `cpu_mhz`, `gpu_config` — keep. `gpu_select.sh verify` must still gate every measured run; the MX230 PCI-id incident (silent fallback to Iris, rows logged as MX230) is a class of bug, not a one-off.

### 3.3 Metrics to add (new columns, appended to `results.py:COLUMNS`)

| Column | Definition — pin it as tightly as `TIER1_CONTRACT.md` pins step size |
|---|---|
| `case_id` | fixed case set identifier. Must be a literal from a versioned manifest. |
| `dataset_sha256` | hash of the input volume. Without this a "regression" may be a changed input. |
| `ingest_wall_s` | file-open dialog dismissed (or CLI `--load` issued) → volume node present in MRML **and** first slice painted. Both halves, or the number moves when rendering changes. |
| `segmentation_runtime_s` | algorithm entry → segmentation node written. Excludes UI. Record `segmentation_dice` alongside or the runtime is meaningless — a fast wrong segmentation is not an improvement. |
| `segmentation_dice` | correctness gate for the above. `benchmark-optimization-loop`: no optimisation without a green correctness gate. |
| `fps_at_volume_mb` | fps is not one number. Capture at ≥3 pinned volume sizes (e.g. 1 mm MNI ~8 MB / a 0.5 mm case / a 4D series) and record which. One `fps_avg` row per size. |
| `peak_ram_mb` (extend) | keep PSS alongside RSS as `glitch_notes` already does — Slicer + Python + Qt share desktop libs and RSS overstates. |
| `installer_size_mb` | packaged installer artifact, distinct from `installed_size_mb` (unpacked tree). Both matter; they differ by compression. |
| `commit_sha` | full sha. `stack` carries the short form for readability. |

Two mechanical consequences of adding columns, both already handled by the code and both easy to trip over:
- `results.append_run` refuses to append to a `runs.csv` whose header differs from `COLUMNS`. Migrating means rewriting the existing header and back-filling 177 rows with empty values — do it once, in one commit, serially.
- `import_results.py` checks the header **exactly**. Any evaluator-side writer (`release/evaluator.ps1`) must be regenerated in the same commit or every import fails.

### 3.4 The nightly comparison rule (the important one)

`TIER0_CONTRACT.md`'s finding — *"ratios travel between batches; milliseconds do not"*, ~1.8× drift across two matrices hours apart with nothing changed — is the single constraint that shapes all NFR automation:

> **A nightly job must never compare tonight's absolute number against last night's.** It must build **both** the baseline commit and HEAD, measure both **in the same batch, back to back**, and report the **ratio**. `run_matrix.sh` already implements exactly this shape — one shared `batch_id`, inner loop over the thing being compared, so the two are adjacent in time. Reuse it with `variant` in place of `stack`.

Everything else follows: absolute NFR targets (a 60 fps gate, a 2 s ingest gate) can only be asserted from a **manually attended, single-sitting** capture, and the numbers in the FYP report must come from such a sitting. The nightly job's job is regression detection, not target verification. Say that in the report.

### 3.5 Optimisation loop

When an NFR misses target, run `benchmark-optimization-loop` literally: baseline → bottleneck from evidence (not intuition) → one hypothesis per variant → same input shape → reject on correctness (`segmentation_dice`, visual PPM diff via the `--dump-frame` mechanism `TIER1_CONTRACT.md` already specifies) → promote → codify in `harness/` → re-measure baseline and winner together in one batch. Variants are measured **serially**; the parallelism is in generating them, not running them.

---

## 4. Local scheduled runner

Per `autonomous-agent-harness`, but grounded: no cloud scheduling, no dispatch endpoint, no API-key-bearing webhooks. Fedora 44 systemd **user** timers plus `claude -p` headless for the reasoning steps. Everything the machine already has.

### 4.1 Jobs

| Job | Schedule | What it does | Reasoning agent? |
|---|---|---|---|
| `braintwin-build` | `02:00` daily | `git fetch`; if HEAD unchanged since last success, exit 0 and log skip. Else configure + build our module against the read-only superbuild; run `ctest`. Writes `state/build-<date>.json`. | No — pure bash. Deterministic. |
| `braintwin-nfr` | `03:00` daily, `Requires=` build success | Builds baseline sha **and** HEAD, runs the fixed case set under both, one shared `batch_id`, appends Tier-2 rows, then `report.py --check --batch <id>`. | No for capture. **Yes** for the summary: one `claude -p` invocation reads `report.py`'s output and writes a 10-line delta note to `results/sessions/`. |
| `braintwin-audit` | `Sun 09:00` weekly | `rpm -q` / `pip list` / CMake `find_package` versions for Slicer, VTK, ITK, CTK, Qt, python deps; diff against `state/deps.lock.json`; check each new/changed dependency's licence against an allowlist. | **Yes** — licence classification is judgement work; that is what `claude -p` is for. Output is a proposal, never a commit. |

`braintwin-nfr` is the one with a real precondition problem: it needs a graphical session. `run_tier1.sh` already refuses to measure on a locked session, and correctly. **At 03:00 the machine is very likely locked.** Options, pick one and write it down: (a) run the NFR job on an explicit `systemd` unit with the session unlocked and screen-blank/lock disabled for the window, (b) move it to a supervised slot (e.g. 13:00 while working), (c) split it — the non-GPU metrics (ingest, segmentation runtime, footprint, installer size, cold start) run headless at 03:00; the fps metrics run only in an attended slot. **(c) is the honest answer** and is what this policy recommends: fps is the metric most damaged by unattended capture anyway, per §3.4.

### 4.2 Where state lives

```
/home/rasikh/Projects/BrainTwin_App/
  results/runs.csv                 # THE ledger. results.py is still the only writer.
  results/agent_runs.csv           # §1.3 fan-out ledger.
  results/sessions/<date>-*.md     # human-readable write-ups, quoting report.py verbatim.
  ops/
    jobs/*.sh                      # the job bodies, in git, reviewable
    state/                         # gitignored, machine-local
      last-success.json            # per job: sha, timestamp, exit code
      deps.lock.json               # tracked in git — it is the audit baseline
      queue.md                     # autonomous-agent-harness task queue, plain markdown
      STOP                         # presence of this file aborts every job. See below.
    logs/<job>-<date>.log
```

Nothing goes in a database. Nothing goes to a cloud scheduler. `deps.lock.json` is tracked because it is the thing being diffed; everything else under `state/` is machine-local and disposable.

### 4.3 Guardrails and stop conditions

Hard rules, all enforced in the job scripts, not remembered:

1. **`ops/state/STOP` exists → every job exits 0 immediately and logs the abort.** A one-file kill switch that needs no daemon and no privileges.
2. **No job commits, pushes, opens a PR, or edits source.** Jobs append to `results/`, write to `ops/state/`, and write proposals to `results/sessions/`. Anything requiring a code change is a queue entry a human reads. This is `autonomous-agent-harness`'s consent boundary applied literally.
3. **Timeout per job** (`systemd` `RuntimeMaxSec=`): build 90 min, NFR 60 min, audit 15 min. Exceeded → SIGTERM, mark `status=invalid` with `status_reason=timeout` on any partial rows. Never delete rows.
4. **Governor and GPU checked up front, run refused on mismatch** — `run_matrix.sh` already does this and documents why ("a warning printed 60 launches into an unattended batch is a warning nobody reads"). Same for `check_env.sh`.
5. **Three consecutive failures of a job disables that job** (write `ops/state/<job>.disabled`, notify, stop trying). Prevents a broken job from filling the disk with 200 identical logs by exam week.
6. **Disk floor**: refuse to start if <20 GB free. A superbuild plus MangoHud CSVs plus two build trees fills a disk quietly.
7. **`claude -p` budget**: one invocation per job, `--max-turns` capped, prompt pinned in `ops/jobs/`. No job spawns sub-agents — §1.1's serial-measurement rule and the cost of an unattended fan-out both forbid it.
8. **Every job's last line is a status write.** A job that dies without writing `last-success.json` is visibly incomplete rather than ambiguously successful — `autonomous-agent-harness`'s "always verify that scheduled tasks completed" constraint.
9. **Jobs never run concurrently.** One `systemd` slice, or a lockfile. Two builds at once is §2's collision list in production.

### 4.4 Bootstrap order

Run each job **manually, in the foreground, three times** before it gets a timer. A job that has never been watched succeed is not automation, it is a scheduled surprise. `autonomous-agent-harness` calls for dry-run plans and local queue files before enabling anything recurring; treat those three manual runs as the dry run.

---

## 5. Limitations and what could go wrong

**On the fan-out rule**
- The §1.3 validation needs ~20 logged decisions. On an FYP timeline you may finish the project before the rule is statistically validated. Treat §1.2's table as a prior derived from the four gates, not as a measured result, until the ledger says otherwise — and say so in the report.
- There is no true counterfactual: you will rarely run the same task both ways. `rework` is the honest signal; wall-clock deltas will be confounded by task difficulty.
- Sub-agents return conclusions, not evidence. G3 exists to stop that being dangerous, but a lane that *looks* deterministic (grep-based) can still return a confidently wrong "not found" because it searched the wrong tree. Spot-check fan-out negatives.
- Token cost of fan-out is real and non-obvious: each lane re-derives project context cold. For a two-lane task the fan-out often costs more tokens *and* more wall clock.

**On worktree isolation**
- The read-only shared superbuild is the recommendation, and it means all lanes share one Slicer/VTK/ITK version. A lane that needs a different VTK cannot use it and must pay the full superbuild. Accept that; do not quietly make the shared prefix writable.
- `XDG_CONFIG_HOME` redirection covers Slicer's settings but is not guaranteed to cover every third-party module's state (some write to hard-coded `$HOME` paths). Verify per module rather than assuming.
- ccache sharing is safe for correctness but can mask a stale-generated-header problem by serving a cached object. If a build behaves impossibly, `CCACHE_DISABLE=1` before believing anything.

**On the benchmark**
- **The largest risk.** The ~1.8× machine-state drift documented in `TIER0_CONTRACT.md` was never root-caused, and it was ruled out as a governor effect by a paired capture. It could equally affect Tier-2 numbers. The batch discipline contains it but does not explain it; a reviewer is entitled to ask what it was and the honest answer is "unknown".
- Tier 1 was never completed for Qt+VTK — one row. Any narrative implying the Qt decision was made on measured Tier 1 evidence would be false. The defensible framing: Tier 0 was measured across all three; Tier 1 established the contract and one implementation; the Qt choice rests on ecosystem/template maturity and the 3D Slicer reference ceiling, which §4 of `docs/03` was always designed to provide.
- MangoHud aborts the host process on timed-log stop (`free(): invalid pointer`), so exit codes cannot judge a run. This will look like a crash to any naive automation. `run_tier1.sh` validates on log contents; anything new must do the same.
- Adding columns to `runs.csv` is a one-way migration touching `results.py`, `import_results.py`, and `release/evaluator.ps1` together. Get it wrong and the evaluator machine's rows silently stop importing.
- `fps_at_volume_mb` multiplies the run count by the number of volume sizes. A nightly attended-slot capture with 3 sizes × 2 vsync modes × 2 variants × 5 runs is 60 × 30 s ≈ 30 minutes of pure capture. Budget it or cut sizes.
- Machine A's 60 Hz panel still pins vsync-on captures at ~60 fps. Every meaningful headroom number needs vsync-off, and the Avalonia row already showed that "vsync off" cannot always be *confirmed*. Confirm it on the Qt path (VTK/Qt exposes a swapchain; ask it) rather than assuming.

**On the scheduled runner**
- The 03:00 locked-session problem is real and is why §4.1 splits the job. If someone "fixes" it by disabling the lock screen on a machine holding medical imaging data, that is a worse outcome than losing the nightly fps number.
- Unattended NFR capture competes with whatever else the machine does at night (backups, `dnf` updates, indexers). Any of these reproduces the drift the batch rule exists to contain — inside a batch, where it is invisible.
- `claude -p` in a cron context runs with no interactive context and can fail in ways that look like success (empty summary, generic text). Job 8's status-write rule catches a dead job, not a vacuous one. Skim the weekly audit output; do not let it become wallpaper.
- Licence classification by a model is a starting point, not a legal answer. The audit's job is to surface *changes*, which is a mechanical and reliable task; the classification attached to them is advisory.
