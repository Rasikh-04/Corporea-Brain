# 11 — Non-functional requirements and the benchmark

The performance and resource requirements from [`07-SRS.md`](07-SRS.md), and how the harness
already built in `~/Projects/BrainTwin_Native` is repurposed to measure them.

<a id="what-it-proves"></a>

## What the harness already proves, and what it does not

Read this before quoting any number from it.

**Established.** Tier 0, the Hello World control, is complete on all three candidate stacks:
40 runs each for Qt+C++, Rust+wgpu and Avalonia, isolating binary size, cold start and idle
RAM from anything rendering-related. Tier 1, the volume-plus-mesh-plus-overlay scene, is
complete for Rust+wgpu across the full four-cell matrix, and on every cell with a real GPU it
passes the criteria: 60 fps average, p95 under 20 ms, p99 under 33 ms — including the
constrained 4 GB, throttled-CPU cell. The software-rasteriser cell fails at about 4 fps, which
is a finding about the workload rather than about any candidate: the task needs a GPU.

**Not established, and this must be stated honestly in the report.** Tier 1 was never completed
for Qt+VTK or Avalonia. The results file holds one Qt+VTK Tier 1 row and zero for Avalonia
against 56 for Rust. **The decision to go with Qt was therefore not made on completed Tier 1
evidence.** It was made on the ecosystem argument — Slicer is already a Qt/C++/VTK application,
so the platform, the imaging toolchain and the intended stack converge on one answer — and on
Tier 0 plus the imaging-ergonomics criterion, where the absence of any medical volume-rendering
template for Rust was itself a finding.

That is a defensible decision. It is not the same claim as "Qt won the benchmark", and writing
it as the latter is the kind of overstatement an examiner finds. See
[`18-POC_INHERITANCE.md`](18-POC_INHERITANCE.md) and
[ADR-003](DECISIONS/ADR-003-application-shell.md).

<a id="batch"></a>

## The batch-comparability constraint

The harness enforces a rule that carries forward and constrains how the application is
benchmarked: **absolute timings on the reference machine are comparable only within one capture
batch.** Cross-batch drift of roughly 1.8x has been observed with no identified cause. The
report tool builds cross-stack tables only from rows sharing a `batch_id`, and keeps `governor`
in each cell's identity so runs at different CPU clock policies are never averaged together.

Two consequences for the application:

1. **Nightly automated runs report ratios, not absolutes.** A nightly job builds the baseline
   and HEAD in one shared batch and reports the delta between them. That is what detects a
   regression.
2. **Every absolute number that reaches the thesis comes from one attended sitting**, with the
   governor pinned to `performance` and the GPU binding verified. NFR values are set from that
   sitting, not from a nightly log.

<a id="schema"></a>

## Schema carried over and extended

The existing 28-column row schema is kept as-is. Renaming would invalidate 177 existing rows
for no gain.

Carried over unchanged: `date`, `batch_id`, `machine_id`, `os`, `tier`, `render_technique`,
`gpu_config`, `ram_cap_gb`, `cpu_config`, `governor`, `cpu_mhz`, `vsync`, `run_index`,
`compile_cold_s`, `compile_warm_s`, `cold_start_s`, `first_frame_s`, `fps_avg`,
`frame_time_p95_ms`, `frame_time_p99_ms`, `peak_ram_mb`, `peak_vram_mb`, `installed_size_mb`,
`glitch_notes`, `pass_fail`, `status`, `status_reason`.

**Reinterpreted rather than renamed:** `stack` becomes the application variant identifier
(`slicer-app`, `slicer-app-py`, `slicer-app-cpp`) rather than a candidate framework.
`tier` gains the value `2`, meaning the application itself, distinct from the Tier 0 control
and the Tier 1 matched scene.

**Added columns for the application:**

| Column | Meaning |
|---|---|
| `stage` | Which pipeline stage this row measures, or `ui` |
| `ingest_wall_s` | Stage 0 to 2, per study |
| `preprocess_wall_s` | Stages 3 to 7 |
| `parcellation_wall_s` | Stage 8 |
| `segmentation_wall_s` | Stage 9 |
| `attribution_wall_s` | Stage 10 |
| `end_to_end_wall_s` | Study on media to attribution on screen |
| `dice_median` | Quality, so a speed optimisation that degrades accuracy is visible in the same row |
| `volume_voxels` | The volume size the fps figure refers to |
| `installer_size_mb` | Distinct from `installed_size_mb` |
| `dataset_hash` | Which case set produced this row |
| `commit_sha` | Exact source state |
| `network_disabled` | Boolean, for the offline test |

**`dice_median` in the performance table is deliberate.** A change that halves segmentation
time and costs three points of Dice must be visible as one fact, not two.

<a id="matrix"></a>

## Test matrix for the application

| Axis | Values |
|---|---|
| Variant | `slicer-app-py` (scripted modules), `slicer-app-cpp` (ported hot paths) |
| Machine | A (Fedora, reference), B-Windows, C (evaluator, no dev tools) |
| GPU config | Integrated only / discrete / software rasteriser (floor) |
| RAM cap | unrestricted / 8 GB / 4 GB |
| CPU | full boost / throttled |
| Tier | 0 control · 1 matched scene · **2 application** |
| Network | enabled / **disabled** |

The 4 GB, throttled, integrated-GPU cell is the decision-relevant one. It is the closest
proxy for the target deployment: a laptop in a resource-constrained clinic.

<a id="reference"></a>

## Reference machine

Machine A, recorded before any stack was built: Fedora Linux, KDE on Wayland, Intel Core
i5-1035G1 (4 cores, 8 threads, 15 W U-series, 0.4 to 3.6 GHz), 15 GiB usable RAM, Intel Iris
Plus G1 integrated GPU, NVIDIA GeForce MX230 with 2 GB VRAM, 1920x1080 at 60 Hz, NVMe.

Two properties of this machine that shape the requirements:

- It is a **15 W part that throttles under sustained load**. Long pipeline stages will interact
  with thermal behaviour. Log sustained-run order in `glitch_notes`.
- It has **2 GB of VRAM**. One volume is not a constraint. Multiple cases loaded at once will
  be, and the timeline comparison view loads two.

<a id="passfail"></a>

## Pass and fail criteria

| # | Criterion | Threshold |
|---|---|---|
| P1 | Interactive 3D | ≥ 30 fps average, p95 frame time < 33 ms, at the declared volume size on the reference machine, integrated GPU |
| P2 | End-to-end pipeline | ≤ `<X>` min per study on the reference machine, `<X>` set from the first attended baseline |
| P3 | Cold start | ≤ `<X>` s to usable UI |
| P4 | Peak RAM | ≤ `<X>` GB, must fit the 4 GB cell in a documented degraded mode |
| P5 | Peak VRAM | Must not exceed 2 GB in the two-case comparison view |
| P6 | Installer size | ≤ `<X>` MB |
| P7 | **Offline** | Full pipeline completes with the network interface disabled. Binary pass or fail. |
| P8 | Reproducibility | Identical input produces byte-identical derived artifacts, checksummed |

Every `<X>` is set from a measured baseline in a single attended batch, then frozen. Guessing a
threshold and then measuring against it is not a requirement, it is a wish.

<a id="offline"></a>

## The offline verification test

This is a headline claim for the target setting, so it is tested deliberately rather than
assumed.

Procedure: disable the network interface at the OS level, not by trusting the application.
Cold-start the application. Import a study from local media. Run the full pipeline to
attribution. Export a report. Re-enable networking. **Any outbound connection attempt during
the run is a failure**, captured by a packet-level check, not by inspection of the code.

Runs as a release gate. See [`17-RELEASE_AND_PACKAGING.md`](17-RELEASE_AND_PACKAGING.md).

<a id="running"></a>

## Running a measurement

```bash
sudo cpupower frequency-set -g performance   # the runner refuses without this
bash bench/gpu_select.sh --verify            # confirms the bound device by name, not by id
bash bench/run_tier2.sh --variant slicer-app-py --gpu iris --ram 4 --cpu throttled --runs 5
python3 bench/report.py --batch <batch_id>
python3 bench/report.py --check              # exit 1 if any cell is untrustworthy
```

Three enforcement rules inherited from the harness, all of them because getting them wrong is
silent:

1. **GPU binding is verified, not assumed.** `MESA_VK_DEVICE_SELECT` falls back to the default
   device without warning on an unmatched PCI id, producing runs that measure the integrated
   GPU while being logged as the discrete one.
2. **The CPU governor is checked before the run**, and the runner refuses to proceed otherwise.
3. **`bench/report.py` is the only code that reads the results file**, so a number in a write-up
   and a number on screen cannot drift apart. It excludes superseded and invalid rows and
   prints the exclusion.

<a id="reporting"></a>

## Reporting

Median is the headline. Run 1 is reported separately, because a first run includes cache
effects that are real but are not the steady state. `glitch_notes` stays free text and is where
a stutter that percentiles catch numerically gets a human description attached.

Every NFR figure in the thesis cites its `batch_id`. A number without one is not admissible.

---

**Related:** [`07-SRS.md`](07-SRS.md) ·
[`10-EVALUATION_PROTOCOL.md`](10-EVALUATION_PROTOCOL.md) ·
[`18-POC_INHERITANCE.md`](18-POC_INHERITANCE.md) ·
[`ai-workflow/A3-PARALLELISM_AND_BENCHMARK_AUTOMATION.md`](ai-workflow/A3-PARALLELISM_AND_BENCHMARK_AUTOMATION.md)
