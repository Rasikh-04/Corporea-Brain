# 14 — Coding standards

Baseline conventions plus the Slicer-specific rules that are not obvious and that cost time
when discovered late.

<a id="versions"></a>

## Language versions and toolchains

| | Version | Pinned where |
|---|---|---|
| C++ | C++17, matching Slicer's requirement at the pinned revision | `CMakeLists.txt` |
| Python | The Python bundled with Slicer, for scripted modules. A separate 3.11+ environment for the offline pipeline | `15-BUILD_AND_ENVIRONMENT.md` |
| CMake | As required by the pinned Slicer revision | `15-BUILD_AND_ENVIRONMENT.md` |
| Qt | Whatever the pinned Slicer superbuild provides. **Never a system Qt.** | Superbuild |

**Do not mix Python environments.** Scripted modules run in Slicer's interpreter. The pipeline
and the evaluation harness run in their own environment. Code shared between them lives in a
small pure-Python package with no Slicer imports, and that constraint is checked by a test.

<a id="cpp"></a>

## C++ rules

Follow the C++ Core Guidelines. The subset that matters most here:

- **Ownership is explicit.** No raw owning pointers. VTK objects use `vtkSmartPointer`; Qt
  objects use parent ownership. Never both on the same object.
- **`vtkNew` for locals, `vtkSmartPointer` for members and returns.** Mixing them is the most
  common lifetime bug in VTK code.
- **RAII for everything else.** No manual `new` and `delete` pairs.
- `const` by default, on parameters, methods and locals.
- No `using namespace` at file scope in a header.
- Prefer `enum class`. A bare enum in a header pollutes.
- No exceptions across a module boundary. Slicer's error convention is return codes plus the
  logging macros; follow it at the seam, use exceptions freely inside your own translation unit.
- Compile with warnings as errors in CI. A warning that is allowed to exist stops being read.

<a id="lifetime"></a>

## VTK and Qt object lifetime

The three rules that prevent most crashes in Slicer extension work:

1. **The MRML scene is touched only from the main thread.** Worker results are marshalled back
   before any node is created, modified or removed. This is not a guideline.
2. **Never store a raw pointer to a MRML node across an event.** The scene can delete it. Hold
   the node id and re-resolve, or hold a smart pointer and understand what that keeps alive.
3. **Disconnect observers in the destructor.** A dangling observer on a scene that outlives your
   widget is a crash at an unrelated moment, which is the worst kind to debug.

<a id="python"></a>

## Python rules for scripted modules

- PEP 8, enforced by a formatter and a linter in CI. No manual style debate.
- **Type hints on every public function.** Checked, not decorative.
- No wildcard imports.
- A scripted module's logic lives in a plain class with **no Slicer imports at module import
  time**, so it can be unit tested headless. The Slicer-facing widget is a thin shell over it.
  This one rule is what makes the module testable at all.
- Long work goes to a CLI module or a subprocess. Never a blocking loop in the widget.
- Every external tool invocation records its full command and version into provenance at the
  point of invocation, not afterwards.

<a id="mrml"></a>

## MRML node conventions

- Node names are for humans; **node ids are for code**. Never look a node up by name.
- Every node we create carries our attribute namespace: `BrainTwin.<key>`. This is how our
  nodes are distinguishable from a user's and from another extension's.
- Every derived node carries `BrainTwin.artifactId` linking it to the `DerivedArtifact` row.
  A node with no artifact id is a leak in the provenance chain.
- Scene state is not a database. The record store is the database. A node holds a reference,
  not the truth.

<a id="naming"></a>

## Naming

| Thing | Convention | Example |
|---|---|---|
| C++ class | `PascalCase`, `qSlicer` or `vtkSlicer` prefix per Slicer convention | `qSlicerRegionAttributionModuleWidget` |
| C++ member | `m_camelCase` | `m_activeParcellation` |
| Python module | `snake_case` | `region_attribution.py` |
| Python class | `PascalCase` | `RegionAttributionLogic` |
| CMake target | `PascalCase` matching the module | `RegionAttribution` |
| Organ id, region id, rule id | lowercase, hyphenated | `ctx-lh-superiorfrontal` |
| Case id | `<source>-<n>` | `brats-001`, `pt-014` |
| Branch | `mod/*`, `pipe/*`, `adr/*`, `bench/*` | `mod/region-attribution` |

**Anatomical identifiers are never invented.** They come from the parcellation, and the region
id in code equals the label id in the atlas equals the node name in the mesh. That equality is
load-bearing and is asserted by a test.

<a id="errors"></a>

## Error handling and the no-silent-failure rule

The rule, stated once:

> **A function that cannot do its job says so. It does not return a default, a zero, an empty
> list, or the input unchanged.**

Specifics:

- No bare `except:` in Python. No swallowed exceptions with a comment saying it is fine.
- No `catch(...)` in C++ that logs at debug and continues.
- **A missing input is `INSUFFICIENT_INPUT`, not a substituted proxy.** This is the single most
  important rule in the codebase for clinical safety, and it is borrowed directly from the ear
  work's rule engine, where a rule that cannot fire records that it could not fire rather than
  weakening its inputs.
- A fallback is allowed only when it is (a) explicit, (b) logged with the reason, and (c) marked
  `DEGRADED` on every downstream output that depends on it.
- An error that reaches the user names the failure class and the specific input responsible.

<a id="logging"></a>

## Logging levels

| Level | Use for | Never contains |
|---|---|---|
| `ERROR` | The operation failed and the user needs to know | PHI |
| `WARNING` | The operation completed degraded, or a fallback was used | PHI |
| `INFO` | Stage boundaries, tool invocations, versions | PHI |
| `DEBUG` | Parameters, intermediate shapes, timings | PHI |

**PHI never appears at any level, including debug.** Log the opaque case id and the artifact
id. Never the source path, which routinely contains a patient name in DICOM exports. A test
asserts this against a PHI-seeded synthetic study. See
[`12-SECURITY_PRIVACY_COMPLIANCE.md`](12-SECURITY_PRIVACY_COMPLIANCE.md).

<a id="cmake"></a>

## CMake conventions

- One module, one directory, one `CMakeLists.txt`.
- **Never modify a superbuild dependency's build.** If something upstream is wrong for us:
  configure, subclass, wrap, work around in our own module, or file it upstream and pin the
  workaround with a comment naming the issue. A local patch to a superbuild dependency is
  unbuildable by the next person.
- Every external dependency is pinned to an exact version or commit. "Latest" is a
  reproducibility failure and it will bite during the write-up.
- Out-of-source builds only. `build/` is git-ignored and is never committed. Note that the
  existing benchmark repository does have build artifacts checked in under
  `stacks/qt-vtk/tier1/build/`; do not copy that pattern here.
- `ccache` is expected and is configured shared across worktrees, because it is
  content-addressed and sharing it is safe and materially faster.

<a id="third-party"></a>

## Third-party code policy

- Prefer an extension over vendoring. Prefer vendoring over copying. Never copy without
  attribution and a recorded licence.
- Any vendored file keeps its header, its licence and a `VENDORED.md` entry naming the source,
  version, date and the reason it was not used as a dependency.
- No dependency is added without a licence register entry in
  [`13-LEGAL_AND_ETHICS.md`](13-LEGAL_AND_ETHICS.md). This is a merge blocker, not a follow-up.

<a id="review"></a>

## Review checklist

Every pull request. If a line cannot be answered, the PR is not ready.

- [ ] Which user story or requirement does this serve?
- [ ] Does it produce or preserve a number that lands in a results table?
- [ ] Does every new derived value carry provenance and uncertainty?
- [ ] Does any new failure path return a default instead of an error?
- [ ] Any PHI reachable in a log, a path, an exception or a test fixture?
- [ ] Any hard-coded colour, font, spacing or icon in a module? (Those belong in a UI bundle.)
- [ ] Any hard-coded atlas, parcellation or coordinate space?
- [ ] Is the MRML scene touched off the main thread anywhere?
- [ ] Are new observers disconnected in the destructor?
- [ ] Any new dependency without a licence register entry?
- [ ] Any data file added under a path that is not git-ignored?
- [ ] Does it cross an architectural seam listed in [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md)?

---

**Related:** [`03-ARCHITECTURE.md`](03-ARCHITECTURE.md) ·
[`15-BUILD_AND_ENVIRONMENT.md`](15-BUILD_AND_ENVIRONMENT.md) ·
[`16-TESTING_STRATEGY.md`](16-TESTING_STRATEGY.md)
