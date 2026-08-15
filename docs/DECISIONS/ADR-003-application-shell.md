# ADR-003 — Application shell is a custom 3D Slicer application

**Status:** Accepted
**Date:** 2026-08-15
**Owner:** Lead
**Supersedes:** The three-way spike proposed in the build plan
**Blocks:** Architecture, build environment, coding standards, testing

## Context

The team's stated stack preference was Qt with C++ and VTK, with Rust and Avalonia held as
alternatives. A benchmark repository was built to decide between them against one matched
brain-visualisation task.

Separately, the build plan observed that **3D Slicer is itself a Qt/C++/VTK application**, built
on VTK, ITK, CTK, CMake, Qt and Python, and that SlicerCustomAppTemplate exists specifically to
produce branded custom applications by setting CMake variables rather than by modifying Slicer
source. Licensing permits it: the template is Apache-licensed, Slicer is BSD-style, both
permissive with attribution, and custom code may be licensed as we choose.

The build plan proposed resolving this with a one-week, three-way spike scored on six criteria.

## Options considered

| Option | Pros | Cons |
|---|---|---|
| **Custom Slicer application** | Intended stack, and the platform, are identical. Inherits DICOM handling, Segment Editor, registration, volume rendering, markups, scene serialisation, installers. Its module architecture **is** the organ plugin system. Python scripted modules mean the whole team contributes on day one | Large inherited codebase to learn. Slow superbuild. Must answer "what did you actually build?" crisply |
| Bare Qt plus VTK from scratch | Full control, no inherited codebase | Rebuilds most of R0 and R1 by hand. Months of work with no evaluated gain |
| Rust with wgpu | Passed Tier 1 on every GPU-bearing cell | **No medical volume-rendering template exists** — itself a recorded finding. No imaging ecosystem. Team would be learning Rust and neuroimaging simultaneously |
| Avalonia on .NET | Cross-platform, a commercial volume-rendering engine exists | Tier 1 never completed. Smallest medical imaging ecosystem of the three |
| Web POC wrapped in Tauri | Reuses working code, cheapest VR path | Wrong architecture for an encrypted longitudinal record; abandons the intended stack |

## Decision

**Build a custom 3D Slicer application via SlicerCustomAppTemplate, in Qt, C++, VTK and Python.
The three-way spike is not run; the decision is taken on the evidence below.**

Original modules are written first as Python scripted modules and ported selectively to C++
loadable modules, **on measured evidence only** — a profiled hot path breaking a stated
non-functional requirement, recorded in the ADR that authorises the port.

## Consequences

**Accepted costs.**
- The superbuild is slow and disk-hungry. First successful build on a new machine is
  realistically a day or two. This is the first risk to retire, in week 1.
- The team must learn MRML, module types and Slicer conventions.
- The "what did you actually build?" question must be answered crisply, every time. The
  contribution sentence exists for this and lives in the README.

**What this closes.** The stack comparison. Reopening requires new measured evidence against a
stated criterion, not a preference.

**What this enables.** Roughly R0 and R1 arrive as configuration rather than construction. The
module architecture becomes the organ registry. Cross-platform installers come from the
platform. SlicerIGT and PLUS make R5 an integration rather than an invention.

## Evidence

**What the benchmark established.** Tier 0, the Hello World control, is complete on all three
stacks at 40 runs each. Tier 1 is complete for Rust with wgpu, which passes 60 fps average,
p95 under 20 ms and p99 under 33 ms on every cell with a real GPU including the constrained
4 GB throttled-CPU cell.

**What it did not establish, stated honestly.** Tier 1 was never completed for Qt+VTK or
Avalonia — the results file holds 56 Tier 1 rows for Rust, one for Qt+VTK and zero for
Avalonia. **This decision is therefore not made on completed Tier 1 rendering evidence.**

It rests on four other grounds, which are stronger for this project than a frame-rate number:

1. **Convergence.** Slicer *is* the intended stack. This is not a compromise between three
   options; it is the option that makes the comparison moot.
2. **What the platform supplies for free**, which is most of R0 and R1.
3. **Imaging and math ergonomics** — one of the benchmark's own four criteria. The absence of
   any medical volume-rendering template for Rust was a recorded finding on exactly this axis.
4. **Team learnability.** Python scripted modules mean contribution on day one.

The build plan's own prediction was that this option wins on everything except VR, and VR is
handled separately by [ADR-009](ADR-009-web-poc-disposition.md).

## Revisit trigger

The superbuild cannot be made to work on any available machine by end of week 2, **or** a
profiled measurement shows the platform cannot meet a stated non-functional requirement that
an alternative demonstrably can.
