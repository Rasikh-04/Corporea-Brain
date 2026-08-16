# 15 — Build and environment

From a clean machine to a running custom Slicer application.

**Do this first, before anything else in the project.** The superbuild is the first technical
risk to retire, not the last. Start it on the strongest machine on day one and work on
something else while it runs.

<a id="machine"></a>

## Machine requirements, honestly

The Slicer superbuild compiles its own dependency tree: VTK, ITK, CTK, Qt, Python and more.

| | Minimum | Comfortable |
|---|---|---|
| Disk free | 60 GB | 100 GB+ |
| RAM | 16 GB | 32 GB. With 16 GB, limit parallel jobs or the linker will be killed. |
| CPU | 4 cores | 8+ cores. This is wall-clock time, directly. |
| First build | Several hours | Realistically **a day or two on a new machine**, including the failures you learn from |

The reference machine (Machine A: i5-1035G1, 15 GiB RAM, ~55 GB free) **can** do this but it is
tight on both disk and RAM. Free disk before starting. Build on the strongest machine
available; the reference machine is for *measuring*, not necessarily for building.

**These figures are this project's own estimates, not an upstream Slicer specification.** The
60 GB is the number to plan against, and it is the only place in this document set that states
a disk minimum. Treat it as a planning figure to be replaced with a measurement once the first
superbuild completes here.

**The 60 GB is a superbuild budget, not a project-wide one.** The development environment,
meaning the pipeline venv and the system packages, costs roughly 8 GB and is independent of it.
`scripts/check-env.sh` gates on the environment budget by default and reports the superbuild
budget as deferred; pass `--superbuild` to gate on that too. Nothing is reserved in advance,
so a machine that cannot yet host the superbuild can still hold a complete, verified
development environment and run everything in `eval/` and `pipeline/` that does not need
Slicer.

<a id="disk-routes"></a>

### Where the 60 GB comes from on Machine A

Measured 2026-08-16. The superbuild is still deferred and this is why.

| Filesystem | Label | Size | Free | Holds |
|---|---|---|---|---|
| `/dev/nvme0n1p3` | Linux | 145.3 GB | 46 GB | `/`, the repository, the venv |
| `/dev/nvme0n1p6` | workspace | 19.4 GB | 18 GB | `/mnt/workspace`, empty |
| `/dev/nvme0n1p4` | Data | 72.8 GB | not mounted | NTFS |
| `/dev/sda2` | HDD | 465.6 GB | not mounted | NTFS, spinning disk |

**A symlink does not pool free space.** `scripts/link-workspace.sh` points `build/` at the
`workspace` partition, which is worth doing for scratch output and ccache, and it does not
move the project any closer to 60 GB: a build that lands there gets 18 GB. `check-env.sh`
measures the filesystem that holds `build/` for exactly this reason, so the number it prints
is the number the superbuild will actually hit.

The routes that do reach 60 GB, in the order they should be considered:

1. **Free 14 GB on `/`.** The shortest path, and the only one that needs no partition work.
   `~/.config` is 17 GB and `~/Projects` is 11 GB on a machine whose active project is 2 GB of
   it. Re-measure with `check-env.sh --superbuild` afterwards rather than assuming.
2. **Grow `workspace` into the `Data` partition.** `nvme0n1p4` is 72.8 GB of NTFS next to the
   19.4 GB `workspace`; shrinking it and growing `nvme0n1p6` gives a dedicated ext4 build
   partition with room to spare. Offline work with gparted, and it is destructive if
   interrupted, so it needs a backup of `Data` first. This is the right long-term answer:
   the superbuild is rebuilt many times over the project and it should not compete with `/`.
3. **Build on the 465 GB HDD.** Space is not the constraint there, everything else is. It is
   NTFS, so case sensitivity, permissions and symlinks all behave differently from what the
   superbuild's external projects expect, and it is a spinning disk, which on a build that is
   already measured in hours is the wrong trade. Reformatting it to ext4 removes the first
   objection and not the second. Last resort.

<a id="fedora"></a>

## Fedora setup

Scripted as [`scripts/setup-env.sh`](../scripts/setup-env.sh), which is idempotent and also
builds the pipeline Python environment. [`scripts/check-env.sh`](../scripts/check-env.sh)
verifies the result and reports the checks it cannot yet run rather than omitting them.

```bash
sudo dnf group install development-tools
sudo dnf install cmake git ninja-build ccache \
  libXt-devel mesa-libGL-devel mesa-libGLU-devel \
  libxcb-devel xcb-util-devel xcb-util-image-devel xcb-util-keysyms-devel \
  xcb-util-renderutil-devel xcb-util-wm-devel libxkbcommon-devel \
  libxkbcommon-x11-devel patch dcm2niix python3.12 python3.12-devel
```

Do **not** install a system Qt and expect Slicer to use it. The superbuild provides Qt. A
system Qt on the path is a common source of a confusing mid-build failure.

### Fedora 44 toolchain, measured 2026-08-15

Fedora ships a toolchain well ahead of what the Slicer superbuild is tested against. Three
of these bite, and none of them announce themselves clearly.

| Component | Fedora 44 ships | Consequence |
|---|---|---|
| CMake | 4.3.0 | CMake 4 removed compatibility with `cmake_minimum_required(VERSION <3.5)`, which superbuild external projects still declare. Configure aborts naming the dependency, not the cause. Mitigate with `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`, or install CMake 3.31.x alongside and put it first on `PATH`. |
| GCC | 16.1.1 | Far ahead of any pinned Slicer revision. Expect compile errors in VTK and ITK from tightened diagnostics. If they appear, pin an older GCC rather than patching upstream — see [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md), what we never modify upstream. |
| Python | 3.14.6 | Irrelevant to the superbuild, which builds its own Python. It **does** block the pipeline environment: see below. |
| Qt | qt5 5.15.18 and qt6 6.11.1, with `qmake` and `qmake6` in `/usr/bin` | Both are on `PATH` by default on a workstation install. This is exactly the trap the paragraph above warns about. |

`dnf groupinstall` is deprecated in favour of `dnf group install`, and the group is now named
`development-tools`. `"Development Libraries"` no longer exists as a group; its contents are
covered by the explicit package list.

<a id="ubuntu"></a>

## Ubuntu setup

```bash
sudo apt update && sudo apt install -y \
  build-essential cmake git ninja-build ccache \
  libxt-dev libgl1-mesa-dev libglu1-mesa-dev \
  libxcb1-dev libxcb-util-dev libxcb-image0-dev libxcb-keysyms1-dev \
  libxcb-render-util0-dev libxcb-icccm4-dev libxcb-xinerama0-dev \
  libxkbcommon-dev libxkbcommon-x11-dev
```

<a id="windows"></a>

## Windows setup

- Visual Studio with the C++ desktop workload, at the version the pinned Slicer revision
  supports. **Not the newest available** — Slicer's supported MSVC version lags.
- CMake and Git, both on `PATH`.
- NSIS if producing an installer.
- **Build in a short path**, for example `C:\bt\`. The superbuild generates deep paths and
  Windows path length limits produce failures that look like unrelated compiler errors.
- Exclude the build directory from real-time antivirus scanning, or the build takes several
  times longer and occasionally fails on a locked file.

<a id="superbuild"></a>

## The Slicer superbuild

```bash
git clone https://github.com/Slicer/Slicer.git
cd Slicer && git checkout <PINNED_REVISION>
cd .. && mkdir Slicer-build && cd Slicer-build
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE:STRING=Release \
  -DSlicer_USE_SYSTEM_QT:BOOL=OFF \
  ../Slicer
ninja
```

`<PINNED_REVISION>` is recorded in this file and nowhere else. Changing it is an ADR, because
it changes every downstream version.

Notes:

- **Release, not Debug**, for the superbuild. A Debug superbuild roughly doubles disk and time.
  Build only our own modules in Debug when needed.
- Do not run `ninja -j$(nproc)` on a 16 GB machine. Linking VTK and ITK in parallel will exhaust
  RAM and the failure looks like a compiler crash. Use `-j4` or fewer.
- Configure `ccache` before the first build. It saves hours on every subsequent rebuild.

<a id="custom-app"></a>

## Building the custom application

Generated from SlicerCustomAppTemplate. Branding, disclaimer, home module, favourite modules
and module removal are all **CMake variables**. We do not edit Slicer source to achieve any of
them.

```bash
git clone https://github.com/KitwareMedical/SlicerCustomAppTemplate.git braintwin-app
# configure per the template's instructions, then:
cmake -G Ninja \
  -DSlicer_DIR:PATH=/abs/path/Slicer-build/Slicer-build \
  -DCMAKE_BUILD_TYPE:STRING=Release \
  ../braintwin-app
ninja
```

Variables we set: application name, organisation, startup disclaimer text, default home module
(the Body Layer), default favourite modules, and the list of built-in modules removed from the
curated set.

<a id="one-module"></a>

## Building one module without rebuilding Slicer

This is the loop you spend your life in. Get it working on day one.

```bash
mkdir -p build/RegionAttribution && cd build/RegionAttribution
cmake -G Ninja -DSlicer_DIR:PATH=/abs/path/Slicer-build/Slicer-build ../../app/Modules/RegionAttribution
ninja
```

Then point Slicer at the built module through the additional module paths setting, or launch
with the module path on the command line.

**Python scripted modules need no build at all.** Edit, then reload from the Slicer developer
tools. This is the main reason every module starts as a scripted module.

<a id="ccache"></a>

## ccache

```bash
export CCACHE_DIR=$HOME/.ccache
ccache --max-size=25G
cmake ... -DCMAKE_C_COMPILER_LAUNCHER=ccache -DCMAKE_CXX_COMPILER_LAUNCHER=ccache
```

The cache is **shared across worktrees deliberately.** It is content-addressed, so sharing is
safe and materially faster when parallel agents or parallel branches build the same headers.

<a id="failures"></a>

## Common build failures

| Symptom | Cause | Fix |
|---|---|---|
| Compiler "killed" or "internal error" during link | Out of RAM from parallel linking | Reduce `-j`. Do not increase swap and hope. |
| Missing xcb or xkbcommon at configure | Distribution packages absent | Install the lists above |
| Qt version mismatch mid-build | A system Qt on `PATH` | Remove it from `PATH`, reconfigure clean |
| Windows: unrelated-looking compiler errors deep in the tree | Path length limit | Rebuild in a short path |
| Module builds but does not appear in Slicer | Module path not registered, or a name mismatch | Check additional module paths; check the CMake target name matches |
| Works on one machine, fails on another | An unpinned dependency | Pin it, then record it here |
| `MESA_VK_DEVICE_SELECT` appears to do nothing | Unmatched PCI id, silent fallback to the default device | Verify by device **name**, per `bench/gpu_select.sh` |
| Configure aborts on `Compatibility with CMake < 3.5 has been removed` | CMake 4.x on Fedora 44 | `-DCMAKE_POLICY_VERSION_MINIMUM=3.5`, or install CMake 3.31.x first on `PATH` |
| `pip install antspyx` builds ITK from source, then fails | System Python is 3.14; antspyx publishes wheels only up to cp313 | Use the Python 3.12 venv from `scripts/setup-env.sh`. Never `pip install` into the system interpreter |
| `pip install nnunetv2` under `--only-binary=:all:` fails to resolve | `acvl-utils` is sdist-only, no wheel published | Do not pass `--only-binary=:all:` for the pipeline set. It is a pure-Python dependency and installs fine from sdist |
| torch pulls ~2.5 GB of CUDA libraries that are never usable | Default PyPI torch is the CUDA build | Install torch from `https://download.pytorch.org/whl/cpu` **before** the requirements file, as `scripts/setup-env.sh` does |
| Superbuild dies partway with no obvious error | Disk exhausted | Check free space against the 60 GB minimum **before** starting: `scripts/check-env.sh --superbuild` |
| `pip install` aborts naming a package that plainly exists | Download timeout on a slow link, reported as if the package were missing | Not a packaging fault. Re-run; pip resumes from its cache. `scripts/setup-env.sh` passes `--retries` and `--timeout` for this reason |

Add a row every time someone loses more than an hour. That is what makes this document worth
keeping.

<a id="python-env"></a>

## Python environment for the pipeline

Separate from Slicer's interpreter, deliberately.

**The interpreter is pinned to Python 3.12.** Not the system Python. `antspyx` publishes
wheels up to cp313 only, so on a cp314 interpreter pip falls back to the sdist and starts
compiling ITK, which fails slowly and confusingly. 3.12 is the newest version with wheel
coverage across the whole set.

```bash
scripts/setup-env.sh              # system packages, ccache, venv, requirements, lock file
scripts/setup-env.sh --no-system  # skip the sudo step
scripts/check-env.sh              # verify
```

What the script does that a bare `pip install -r` does not:

1. Creates the venv against `python3.12` explicitly, and fails loudly if it is absent.
2. Installs `torch` from the CPU-only index **first**, so the resolver cannot pull the CUDA
   build. The reference machine's discrete GPU is an MX230 with 2 GB VRAM, which cannot hold
   nnU-Net 3D inference; the CUDA build would cost ~2.5 GB of disk to be unusable.
3. Writes `pipeline/requirements.lock.txt` from `pip freeze` afterwards.

[`pipeline/requirements.txt`](../pipeline/requirements.txt) holds the direct dependencies,
every pin exact. The lock file holds the full transitive tree and is the actual
reproducibility artifact; both are committed. "Latest" here silently changes results between
runs, which is a reproducibility failure that surfaces during the write-up when it is most
expensive.

Three entries are deliberately unpinned and marked `PLACEHOLDER` in the requirements file,
because pinning them would be inventing a decision that has not been made: the parcellation
backend and the defacing tool, both blocked on [ADR-006](DECISIONS/ADR-006-coordinate-space-and-atlas.md),
and the record store driver, blocked on [ADR-007](DECISIONS/ADR-007-record-store.md).

<a id="verify"></a>

## Verifying the install

Run these in order. Each one has caught a real problem.

1. Launch the custom application. The disclaimer appears **before** any data can be loaded.
2. The home module is the Body Layer, not a Slicer module.
3. Load the sample volume from the benchmark assets. It renders.
4. Run the orientation assertion against the synthetic asymmetric phantom. It passes.
5. Run the evaluation harness known-answer test: two synthetic masks, hand-computed Dice.
6. Run the organ manifest validator. It reports at least the brain manifest as valid.
7. Disconnect the network. Repeat steps 3 to 6. Everything still works.

If step 4 or step 5 fails, stop. Nothing built on top of a broken orientation or a broken
metric is worth anything, and both failures are silent.

<a id="differs"></a>

## When a machine differs

Before quoting a number measured somewhere else, check what the difference invalidates.
Hardware and toolchain differences invalidate specific figures and leave others intact — GPU
differences invalidate fps and VRAM but not installer size; a different CPU invalidates
compile and wall times but not correctness. Record every machine's specification in
`bench/machines/`, and never mix machines within a single reported batch.

---

**Related:** [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md) ·
[`11-NFR_AND_BENCHMARK.md`](11-NFR_AND_BENCHMARK.md) ·
[`16-TESTING_STRATEGY.md`](16-TESTING_STRATEGY.md) ·
[`21-RISK_REGISTER.md`](21-RISK_REGISTER.md)
