# scripts/

Environment setup, CI checks, superbuild monitoring and dataset downloaders.

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
| `build-status.sh` | One superbuild report: progress, target rate, ETA, disk | While the superbuild runs |
| `build-watchdog.sh` | Silent watch that exits when the superbuild needs a human | Armed alongside a long superbuild |
| `make_phantom.py` | Writes the orientation phantom to disk for manual inspection | When eyeballing orientation in a viewer |
| `validate_organs.py` | Validates every organ manifest against the schema | CI, every pull request |

`lib/superbuild-probe.sh` holds the detection helpers the two build scripts share. It is
sourced, never run directly.

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

## build-status.sh and build-watchdog.sh

```bash
scripts/build-status.sh                  # one report, then exit
scripts/build-watchdog.sh &              # arm; stays silent until something is wrong
```

The superbuild runs for hours unattended, and the two ways it goes wrong are both quiet: it
dies and nothing says so, or it keeps running while free disk drains toward zero. The watchdog
covers four cases and **exits** on any of them, so the process ending is the alert:

| Exit | Reason | Means |
|---|---|---|
| 10 | `DISK_LOW` | Free space fell below the floor, build still alive. Act now. |
| 11 | `NEW_FAILURE` | A `FAILED:` line appeared past the watermark taken at arm time. |
| 12 | `PROCESS_GONE` | The outer ninja vanished: finished, killed, or OOM-reaped. |
| 13 | `LOG_STALE` | The log stopped moving while the process lives. A hang. |

Two behaviours are deliberate and worth keeping:

- **It refuses to arm when no build is running**, rather than firing `PROCESS_GONE` a second
  later and reporting a finished build as an incident.
- **On failure it greps a window around the failing line, never the log tail.** The tail of
  this build is dense with C++20 warnings and the real error routinely sits dozens of lines
  above it, which is recorded as a trap in
  [`docs/15`](../docs/15-BUILD_AND_ENVIRONMENT.md#failures).

Nothing is pinned to a run: the ninja process, both progress counters and their totals are
discovered from the build tree. State goes to `$BUILD_DIR/.monitor/`, inside a git-ignored
`*-build/` directory, so it dies with the tree it describes.

## No dataset downloaders exist yet

The datasets in [`docs/10`](../docs/10-EVALUATION_PROTOCOL.md#datasets) have registration or
data-use-agreement lead times measured in weeks. Downloaders land when the agreements do.
