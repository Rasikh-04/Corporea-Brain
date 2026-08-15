#!/usr/bin/env python3
"""Write the orientation phantom to disk, for looking at it in a viewer.

The phantom itself is a deterministic function in
``pipeline/corporea_pipeline/phantom.py``, not a committed file. See that module for why.
Nothing in CI needs this script: the tests build the phantom in memory.

What this is for is the exercise ``docs/06-IMAGING_PIPELINE.md`` asks for by hand, once, and
written down: open a volume, verify that left is left in three independent tools, record how
you verified it, then deliberately break the orientation and observe how invisible the failure
is. ``--break-axis`` produces the broken volume for the second half of that.

Usage:
    scripts/make_phantom.py --out build/phantom.nii.gz
    scripts/make_phantom.py --out build/phantom-broken-lr.nii.gz --break-axis 0

The default output is under ``build/``, which is git-ignored. Rule 8 and the .gitignore rules
for imaging formats apply to this output like any other volume, synthetic or not.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "pipeline"))

from corporea_pipeline.phantom import (  # noqa: E402
    break_orientation,
    build_phantom,
    orientation_report,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=REPO_ROOT / "build" / "phantom.nii.gz",
        help="output path (default: build/phantom.nii.gz, git-ignored)",
    )
    parser.add_argument(
        "--break-axis",
        type=int,
        choices=(0, 1, 2),
        default=None,
        help="flip the data along this voxel axis and leave the affine alone, producing the "
        "deliberately broken volume. Never use the output for anything but the exercise.",
    )
    args = parser.parse_args(argv)

    import nibabel as nib

    phantom = build_phantom()
    data, affine = phantom.data, phantom.affine
    if args.break_axis is not None:
        data, affine = break_orientation(data, affine, args.break_axis)

    report = orientation_report(data, affine)
    print(report.describe())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    nib.save(nib.Nifti1Image(data, affine), args.out)
    print(f"\nwrote {args.out}")

    if args.break_axis is not None:
        print(
            "\nThis volume is deliberately wrong. Open it beside the unbroken one and note "
            "how little there is to see."
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
