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
a disk minimum.

**Measured 2026-08-17, on the first superbuild to complete on Machine A: the finished tree is
6.9 GB**, being 6.7 GB of `Slicer-build/` and 199 MB of the `Slicer/` source clone. The largest
components are VTK at 2.1 GB across source and build, the inner Slicer build at 1.3 GB, the
built Python at 1.3 GB, and ITK at 616 MB.

That is roughly a ninth of the planning figure, for three reasons that all have to hold: the
superbuild is **Release**, it uses **system Qt** rather than building Qt, and **ccache** is
active. A Debug build, or a platform where Qt has to be built, lands in a different order of
magnitude, which is what the 60 GB was defending against.

Two honest caveats. This is the size of the *finished* tree, not the *peak* during the build,
which was never sampled and is higher wherever intermediate objects outlive their install
step. And it is one machine and one configuration. Keep 60 GB as the planning minimum for an
unknown machine; use 6.9 GB when reasoning about this one.

**The 60 GB is a superbuild budget, not a project-wide one.** The development environment,
meaning the pipeline venv and the system packages, costs roughly 8 GB and is independent of it.
`scripts/check-env.sh` gates on the environment budget by default and reports the superbuild
budget as deferred; pass `--superbuild` to gate on that too. Nothing is reserved in advance,
so a machine that cannot yet host the superbuild can still hold a complete, verified
development environment and run everything in `eval/` and `pipeline/` that does not need
Slicer.

<a id="disk-routes"></a>

### Where the 60 GB comes from on Machine A

Measured 2026-08-16, when the superbuild was still deferred and this was why. Kept as the
record of how the budget was reasoned about; the superbuild has since completed on this
machine at a fraction of the cost, as recorded above.

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

**Correction, verified 2026-08-16 against the pinned `v5.12.3` source directly.** Contrary to what
this document used to say: **the superbuild does not provide Qt.** `CMakeLists.txt` always calls
`find_package(Qt5 or Qt6)` against an existing installation; `Slicer_USE_SYSTEM_QT` only affects
RPATH and launcher settings, not whether Qt is built. A system Qt is *required*, not a trap.

Fedora 44 ships Qt5 as runtime-only, with no CMake config files — `find_package(Qt5)` cannot
succeed no matter what is on `PATH`. It ships a complete Qt6 dev stack instead, and Slicer
5.12.3 supports Qt6 (needs 6.8+) when pointed at it explicitly:

```bash
sudo dnf install qt6-qtsvg-devel qt6-qt5compat-devel qt6-qtscxml-devel \
  qt6-qtwebengine-devel qt6-qtwebchannel-devel
```

`qt6-qtbase-devel` and several other Qt6 modules are already present on a typical Fedora 44
workstation install; the five above are the ones Slicer's `Slicer_REQUIRED_QT_MODULES` list
needs that are not. Configure with `-DQt6_DIR:PATH=/usr/lib64/cmake/Qt6
-DSlicer_USE_SYSTEM_QT:BOOL=ON` — see the superbuild command below.

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
cd Slicer && git checkout v5.12.3
cd .. && mkdir Slicer-build && cd Slicer-build
cmake -G Ninja \
  -DCMAKE_BUILD_TYPE:STRING=Release \
  -DSlicer_USE_SYSTEM_QT:BOOL=ON \
  -DQt6_DIR:PATH=/usr/lib64/cmake/Qt6 \
  -DCMAKE_POLICY_VERSION_MINIMUM=3.5 \
  ../Slicer
ninja -j4
```

**Pinned revision: `v5.12.3`** (commit `9034c71a8fce68ab312458b3d7d16f610562263d`), decided in
[ADR-010](DECISIONS/ADR-010-slicer-pinned-revision.md). Recorded in this file and in that ADR.
Changing it is a new ADR, because it changes every downstream version.

The `-DCMAKE_POLICY_VERSION_MINIMUM=3.5` flag works around the Fedora 44 CMake 4.x trap in the
table below. The `-j4` caps parallel linking for machines under the 16 GB RAM comfortable
minimum — see the same table. `-DQt6_DIR` and `-DSlicer_USE_SYSTEM_QT:BOOL=ON` are the Fedora 44
Qt6 route explained in the Fedora setup section above; a platform with a real Qt5 dev install
(Ubuntu, for instance) does not need either override.

Notes:

- **Release, not Debug**, for the superbuild. A Debug superbuild roughly doubles disk and time.
  Build only our own modules in Debug when needed.
- Do not run `ninja -j$(nproc)` on a 16 GB machine. Linking VTK and ITK in parallel will exhaust
  RAM and the failure looks like a compiler crash. Use `-j4` or fewer.
- Configure `ccache` before the first build. It saves hours on every subsequent rebuild.

<a id="watching-the-build"></a>

### Watching a running superbuild

The build runs for hours and both of its failure modes are quiet. It dies and nothing announces
it, or it keeps running while free disk drains toward zero. Watching a terminal for either is
not a plan, and the log tail is actively misleading, for the reason recorded under
[common build failures](#failures).

```bash
scripts/build-status.sh        # one report: progress, target rate, ETA, disk
scripts/build-watchdog.sh &    # arm; silent until something needs a human
```

The watchdog exits on `DISK_LOW`, `NEW_FAILURE`, `PROCESS_GONE` or `LOG_STALE`, so the process
ending is the alert. It refuses to arm when no build is running, and on failure it reports a
window around the failing line rather than the tail. Both scripts discover the ninja process
and the progress counters from the build tree, so neither is pinned to a machine or a run.
See [`scripts/README.md`](../scripts/README.md) for exit codes.

The first measured run on Machine A, after both traps below were fixed, took **2 h 04 min** of
wall clock for the inner Slicer build at roughly 25 to 40 targets per minute on `-j4`, and the
finished tree was 6.9 GB.

<a id="pythonqt-wrappers"></a>

### PythonQt wrapper generation on Qt 6

First hit on 2026-08-17, roughly four hours into a clean superbuild on Machine A. Recorded here
because the error message names the wrong thing and costs an evening if taken at face value.

**Symptom.** The superbuild reaches CTK, then dies:

```
CMake Error at CMakeLists.txt:180 (message):
  PythonQt: missing generated wrapper sources for Qt 6.11.
  Expected: .../CTK-build/PythonQtGenerator-output-6.11.1/generated_cpp
```

**What is actually wrong.** PythonQt ships pre-generated wrappers only for Qt 5.15
(`generated_cpp_515`). For Qt 6 it sets `PythonQt_GENERATED_PATH` to `NOTFOUND` and depends on
CTK building and running `PythonQtGenerator` to produce them. The generator does build, and it
does run, but CTK invokes it with `--output-directory` alone and no `--include-paths`. Its
bundled preprocessor (simplecpp) therefore runs with an empty include path and cannot find
glibc or libstdc++ headers, so Qt's own configuration headers fail on symbols they expect the
system to supply:

```
qconfig.h:19:  #error "unexpected value for __WORDSIZE macro"
qtypes.h:273:  #error Unsupported platform (unknown value for SIZE_MAX)
qnumeric.h:73: syntax error: failed to evaluate #if condition, division/modulo by zero
```

The generator then reports `Classes in typesystem: 0`, writes no output directory, **and exits
0**. Because the exit code is clean, CTK's launcher declares the step successful and the build
carries on until PythonQt's configure step trips over the directory that was never created.
The tell is one line in `CTK-build/PythonQt_GenerateWrapper_step_output.txt`:

```
PreProcessing - Generate [.preprocessed.tmp] using [...] and include-paths []
```

An empty `.preprocessed.tmp` in `CTK-build/PythonQtGenerator-build/` confirms it.

**The fix.** Two edits to `Slicer-build/CTK-build/PythonQtGenerator-launcher.cmake`, both marked
`LOCAL PATCH (BrainTwin_Desktop)`:

1. Pass `--include-paths` covering `/usr/include/qt6` and its module directories, the GCC C
   headers, and `/usr/include`. Each path is existence-checked first, so a toolchain upgrade
   warns by name rather than producing another silent empty parse.
2. Assert after the run that `generated_cpp` exists and holds at least one `.cpp`. This closes
   the exit-zero hole, so the next occurrence fails at the generator with the cause in view
   instead of in a later configure step.

**What must be left out, and why.** Do **not** add `/usr/include/c++/<ver>` or its
subdirectories. This is the second trap, and it costs another cycle if you assume more include
paths are strictly better. `generator/main.cpp:228` hardcodes `__cplusplus=1`, declaring the
parse pre-C++98, and `main.cpp:258` deliberately discards `MISSING_HEADER` diagnostics with the
comment *"we are not interested"*. The generator is built to parse Qt headers only and to let
standard library includes fail silently. Put libstdc++ within reach and those headers resolve,
then immediately reject the very macro state the generator declares:

```
c++0x_warning.h:32: #error This file requires ... -std=c++11
c++config.h:2537:   undefined function-like macro invocation: __has_builtin( ... )
```

Result is another zero-class parse. The glibc and GCC **C** headers are required, though, since
Qt's own `qconfig.h` and `qtypes.h` need `__WORDSIZE` and `SIZE_MAX`. C headers in, C++ headers
out. Regenerate the toolchain half of the list with:

```bash
echo | g++ -xc++ -E -v - 2>&1 | sed -n '/search starts here/,/End of search list/p'
```

then keep only `/usr/lib/gcc/.../include`, `/usr/local/include` and `/usr/include` from it.

**A clean stderr is not the success signal.** Even on a fully successful run the generator
still prints `#error` lines from `qsystemdetection.h`, `qcompilerdetection.h`, `qtypes.h` and
`qstdlibdetection.h`, because simplecpp defines neither `__linux__` nor `__GNUC__` nor a
standard library. These are non-fatal; simplecpp records them and continues. Judge the run by
`Classes in typesystem:` in the **output** file, never by the error file being empty.

**This patch lives in the build tree, not in the repo.** `PythonQtGenerator-launcher.cmake` is
generated by CTK from `CTK/CMakeExternals/PythonQt.cmake` through `file(CONFIGURE ...)`. It
survives an ordinary resume, because nothing re-runs CTK's configure step. It does **not**
survive a CTK reconfigure or a clean build tree, and the symptom on losing it is the original
misleading error. If that happens, re-apply the two edits before doing anything else. Moving
the fix upstream into `CMakeExternals/PythonQt.cmake` is the durable option and is worth doing
if this recurs, at the cost of a CTK reconfigure and patch-maintenance against a pinned
upstream checkout.

**Outcome, measured 2026-08-17.** With the corrected paths the generator completes in about six
seconds:

```
Classes in typesystem: 810
Generated:  - header: 792 (792)   - impl: 792 (792)   - pri: 13 (13)
```

92 files, 14 MB, across 13 module directories. `QObject`, `QWidget`, `QApplication` and
`QPushButton` are wrapped; `QString` and `QVariant` correctly appear as builtin value types in
`com_trolltech_qt_core_builtin` rather than as `PythonQtWrapper_` classes.

Against the shipped Qt 5.15 baseline (`generated_cpp_515`, 16 modules, 109 files) three modules
are absent, all expected: `webkit` and `xmlpatterns` no longer exist in Qt 6, and `opengl` is
not reachable because the generator's master include never pulls in `QtOpenGL`. Treat 13
modules and roughly 800 classes as the known-good shape. A run that yields far fewer means the
preprocessor stopped early.

**Risk that did not materialise.** PythonQt is pinned at `patched-v4.1.0-2026-06-05-9992368e9`,
whose newest commit is *cmake: Add 6.10 support*, while Fedora 44 ships Qt 6.11.1. The concern
was that one minor version of drift would defeat the parse. It did not: the failure was
entirely in how CTK invokes the generator, not in Qt 6.11 itself, and no Qt downgrade is
needed. If a future Qt genuinely does break the parse, the fallback is a side-installed Qt 6.10
selected through `-DQt6_DIR`, which is a revisit trigger for
[ADR-010](DECISIONS/ADR-010-slicer-pinned-revision.md).

<a id="curl-idn2"></a>

### Static curl and libidn2

First hit on 2026-08-17, in the inner Slicer build at roughly target 500 of 4284. An upstream
Slicer bug that only fires on distributions carrying `libidn2-devel`, which is why it is not
widely reported.

**Symptom.** `libRemoteIO.so` fails to link:

```
libcurl.a(idn.c.o): in function `Curl_idn_decode':
  undefined reference to `idn2_check_version'
  undefined reference to `idn2_lookup_ul'
  undefined reference to `idn2_to_unicode_8z8z'
```

**What is actually wrong.** Slicer builds its own **static** curl and means to disable IDN.
`SuperBuild/External_curl.cmake` passes `-DHAVE_LIBIDN2:BOOL=OFF`, but that is curl's
*detection result* variable, not its toggle. The option curl obeys is `USE_LIBIDN2`, which
Slicer never sets, so it keeps its default of `ON`:

```
HAVE_LIBIDN2:BOOL=OFF     what Slicer sets, ineffective
USE_LIBIDN2:BOOL=ON       what curl actually reads
```

curl's pkg-config check then finds Fedora's `/usr/lib64/libidn2.so` and compiles `idn.c` with
IDN support. Because `libcurl.a` is a static archive it carries no dependency record, and
Slicer links it without `-lidn2`, so the symbols never resolve. On a machine without
`libidn2-devel` the detection fails, IDN is compiled out, and the bug is invisible.

**The fix.** Set the variable curl actually reads, then reinstall. This is a build-tree change,
not an upstream edit, so it stays inside the policy in
[`03-ARCHITECTURE.md`](03-ARCHITECTURE.md):

```bash
cd Slicer-build/curl-build
cmake -DUSE_LIBIDN2:BOOL=OFF .
cmake --build . --target install -- -j4
nm -u ../curl-install/lib/libcurl.a | grep -c idn2   # must print 0
```

Confirm by the configure summary line: the `Features:` list must no longer contain `IDN`. The
outer build then relinks `libRemoteIO.so` on its own, because the refreshed `libcurl.a` is
newer than the failed target. curl's ExternalProject stamps are left untouched deliberately;
nothing needs to re-download or re-clone.

**Note for a clean rebuild.** This fix lives in `curl-build/CMakeCache.txt` and dies with the
build tree. On a from-scratch superbuild the link will fail the same way at the same point.
Either re-apply it when it appears, or pre-empt it by adding `-DUSE_LIBIDN2:BOOL=OFF` to the
curl arguments before the first build.

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
| Configure aborts: `Qt 5.15 was not found on your system` | Fedora 44 ships Qt5 runtime-only, no CMake config files. `find_package(Qt5)` cannot succeed regardless of `PATH` | Build against Qt6 instead: install the five packages in the Fedora setup section above, then configure with `-DQt6_DIR:PATH=/usr/lib64/cmake/Qt6 -DSlicer_USE_SYSTEM_QT:BOOL=ON` |
| `pip install` aborts naming a package that plainly exists | Download timeout on a slow link, reported as if the package were missing | Not a packaging fault. Re-run; pip resumes from its cache. `scripts/setup-env.sh` passes `--retries` and `--timeout` for this reason |
| `libRemoteIO.so` fails to link, `undefined reference to idn2_*` from `libcurl.a` | Slicer sets `HAVE_LIBIDN2=OFF`, which is curl's detection result, not its toggle. curl obeys `USE_LIBIDN2`, defaults it `ON`, finds Fedora's libidn2, and the static archive is then linked without `-lidn2` | Rebuild curl with `-DUSE_LIBIDN2:BOOL=OFF`. See [Static curl and libidn2](#curl-idn2) |
| PythonQt configure aborts: `missing generated wrapper sources for Qt 6.11` | CTK runs PythonQtGenerator with an empty include path, so its preprocessor parses zero classes, writes nothing, and still exits 0. The error you see is two steps downstream of the real fault | Pass `--include-paths` in the generator launcher, with Qt and the C headers but **not** libstdc++. See [PythonQt wrapper generation on Qt 6](#pythonqt-wrappers) |

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
