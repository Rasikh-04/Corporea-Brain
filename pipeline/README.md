# pipeline/

Preprocessing, segmentation and batch jobs. Runs outside Slicer, in its own Python
environment.

Specified by [`docs/06-IMAGING_PIPELINE.md`](../docs/06-IMAGING_PIPELINE.md). Environment
defined by [`docs/15-BUILD_AND_ENVIRONMENT.md`](../docs/15-BUILD_AND_ENVIRONMENT.md).

## What lives here

| Path | Holds |
|---|---|
| `requirements.txt` | Direct dependencies, exact pins. The file a human edits. |
| `requirements.lock.txt` | Full transitive tree. The reproducibility artifact. Generated. |
| `corporea_pipeline/orientation.py` | Anatomical side from an affine, and the assertion. |
| `corporea_pipeline/phantom.py` | The synthetic asymmetric phantom, deterministic. |
| `tests/` | Unit tests. Fast, headless, no Slicer import, no data files. |

## The environment

Python 3.12, not the Fedora 44 system Python 3.14. `antspyx` publishes no cp314 wheel and pip
falls back to compiling ITK from source without saying so. Set up with
[`scripts/setup-env.sh`](../scripts/setup-env.sh), verified with
[`scripts/check-env.sh`](../scripts/check-env.sh).

Do not mix environments. Scripted modules run in Slicer's interpreter; the pipeline and the
harness run here. Code shared across the boundary lives in `app/corporea_core/`.

## Orientation comes first

[`docs/06`](../docs/06-IMAGING_PIPELINE.md#orientation) says to read its orientation section
twice, and it is right. A left/right flip produces a lesion in the wrong hemisphere and every
downstream output is then confidently wrong while looking completely normal.

`orientation.py` and `phantom.py` are the control, and they were written before any stage that
touches geometry. See [`docs/06`](../docs/06-IMAGING_PIPELINE.md#orientation) and
[`docs/16`](../docs/16-TESTING_STRATEGY.md#orientation).

## Stages, and where they are

Stage numbering follows [`docs/06`](../docs/06-IMAGING_PIPELINE.md#overview). Stages 0 to 12
are specified; none are implemented. Stages 3, 6, 7 and 8 touch geometry and are gated on the
orientation assertion. Stages 7 and 8 are additionally blocked on
[ADR-006](../docs/DECISIONS/ADR-006-coordinate-space-and-atlas.md), which is open: nothing here
may name a parcellation, an atlas or a coordinate space until it closes.

## Running the tests

```bash
.venv/bin/python -m pytest pipeline/tests -q
```
