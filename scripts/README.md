# scripts/

Environment setup, CI checks and dataset downloaders.

## Rule 8 applies to this directory more than any other

> **Never commit patient-derived data. Downloader scripts only, never the data.**

Dataset use agreements forbid redistribution and a public repository is a breach. Every script
here that touches a dataset fetches it into a git-ignored path. If you add one, the path it
writes to is a review item on the pull request.

## What lives here

| Script | Does | Run when |
|---|---|---|
| `setup-env.sh` | Idempotent system packages and the Python 3.12 pipeline venv | Once per machine |
| `check-env.sh` | Verifies the environment against [`docs/15`](../docs/15-BUILD_AND_ENVIRONMENT.md) | Before building, and in CI |
| `make_phantom.py` | Writes the orientation phantom to disk for manual inspection | When eyeballing orientation in a viewer |
| `validate_organs.py` | Validates every organ manifest against the schema | CI, every pull request |

## check-env.sh

```bash
scripts/check-env.sh               # gate on the development environment only
scripts/check-env.sh --superbuild  # also gate on the Slicer superbuild disk budget
```

Disk is checked against whichever budget you are about to spend. The superbuild's 60 GB is
reported as deferred rather than failed, so a machine short on disk can still hold a complete,
verified development environment.

Checks that cannot yet run are printed as `SKIP` with the reason. **A check that quietly does
not run is worse than one that fails**, so nothing is omitted silently.

## No dataset downloaders exist yet

The datasets in [`docs/10`](../docs/10-EVALUATION_PROTOCOL.md#datasets) have registration or
data-use-agreement lead times measured in weeks. Downloaders land when the agreements do.
