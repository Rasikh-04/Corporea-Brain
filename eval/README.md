# eval/

The evaluation harness. Metrics, results tables, batch runs.

Specified by [`docs/10-EVALUATION_PROTOCOL.md`](../docs/10-EVALUATION_PROTOCOL.md), tested per
[`docs/16-TESTING_STRATEGY.md`](../docs/16-TESTING_STRATEGY.md).

## Why this exists before the segmenter

Rule 7: build the measuring instrument before the thing it measures. A team that builds the
segmenter first discovers in week 30 that its pipeline was broken in week 10, and there is no
time left to fix it.

A broken metric is worse than a broken segmenter, because it produces plausible numbers. This
is why the known-answer test on hand-computed Dice was the first line of code in this
directory.

## What lives here

| Path | Holds |
|---|---|
| `corporea_eval/metrics.py` | Dice, HD95, ASSD, volume error. Surface distances in millimetres. |
| `tests/test_metrics_known_answer.py` | Hand-computed answers, worked out in the docstrings. |
| `tests/test_metrics_degenerate.py` | Empty, single-voxel and disjoint inputs. No silent NaN. |
| `tests/test_seam_no_application_import.py` | Asserts seam 4 mechanically. |

## Seam 4 is enforced, not trusted

> The evaluation harness never imports the application.

It runs against CLI modules and file artifacts, so results reproduce without a GUI. The seam
is asserted by a test that imports every `corporea_eval` module and fails if `slicer`, `vtk`,
`ctk`, `qt` or anything under `corporea_core` appears in `sys.modules` afterwards.

## What a metric returns

Never a bare float. Every metric returns a result object carrying the value **and** a
`degeneracy` flag, because the degenerate cases are where a metric lies:

- Both masks empty: Dice is `0/0`. Reported as `1.0` with `BOTH_EMPTY`, never averaged in
  silently.
- One mask empty: there is no surface, so HD95 and ASSD are genuinely undefined. Reported as
  `None` with a flag, never as `0.0`, which would read as a perfect score.

Aggregation refuses to average over a `None` without being told which policy to apply. See
`metrics.py` for the full table.

## Running it

```bash
.venv/bin/python -m pytest eval/tests -q
```

## Not built yet

Results-table writers for tables 4.1 to 4.6 in
[`docs/10`](../docs/10-EVALUATION_PROTOCOL.md#tables), Bland-Altman for volume error, and the
batch runner. The metrics and their tests come first.
