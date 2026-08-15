# bench/

The non-functional-requirement benchmark, inherited from `~/Projects/BrainTwin_Native` and
repurposed to measure this application.

Specified by [`docs/11-NFR_AND_BENCHMARK.md`](../docs/11-NFR_AND_BENCHMARK.md). Inheritance
terms in [`docs/18-POC_INHERITANCE.md`](../docs/18-POC_INHERITANCE.md).

## Read this before quoting any number from it

The inherited harness established Tier 0 across all three candidate stacks, and Tier 1 for
Rust and wgpu across the full matrix. **Tier 1 was never completed for Qt and VTK or for
Avalonia.** The stack decision was therefore not made on completed Tier 1 evidence; it was
made on the ecosystem argument and on Tier 0. Writing it as "Qt won the benchmark" is an
overstatement an examiner finds. See
[`docs/11`](../docs/11-NFR_AND_BENCHMARK.md#what-it-proves) and
[ADR-003](../docs/DECISIONS/ADR-003-application-shell.md).

## The batch-comparability constraint

Absolute timings on the reference machine are comparable only **within one capture batch**.
Cross-batch drift around 1.8x has been observed with no identified cause. Two consequences,
both binding:

1. Headline numbers come from a single attended sitting.
2. The development machine is the reference machine, so **a build or a pipeline job running
   during a capture invalidates it.** Check before you start.

The performance regression gate therefore builds baseline and HEAD in one shared batch and
compares ratios, never absolute thresholds. See
[`docs/16`](../docs/16-TESTING_STRATEGY.md#perf-gate).

## Status

Nothing has been ported into this directory yet. The inherited harness still lives in
`~/Projects/BrainTwin_Native` and there is nothing here to run against until the application
builds.

Note that the inherited repository has build artifacts checked in under
`stacks/qt-vtk/tier1/build/`. Do not copy that pattern here;
[`docs/14`](../docs/14-CODING_STANDARDS.md#cmake) forbids it.
