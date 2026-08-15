#!/usr/bin/env python3
"""Validate every organ manifest. Runs in CI on every pull request; failure blocks merge.

``docs/04-ORGAN_MODULE_SPEC.md``, validation. The logic lives in
``app/braintwin_core/organ_manifest.py`` so the application's ``OrganRegistry`` and this script
apply exactly one definition of valid. A CI check that disagrees with the runtime is worse
than no CI check, because it is trusted.

Usage:
    scripts/validate_organs.py [--organs DIR]

Exit code 0 if every manifest is valid, 1 otherwise. Deferred checks are printed and do not
affect the exit code: they are checks that cannot run yet, not checks that passed.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "app"))

from braintwin_core.organ_manifest import validate_directory  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--organs",
        type=Path,
        default=REPO_ROOT / "organs",
        help="directory holding <organ>/manifest.yaml (default: organs/)",
    )
    args = parser.parse_args(argv)

    if not args.organs.is_dir():
        print(f"FAIL  {args.organs} is not a directory", file=sys.stderr)
        return 1

    reports = validate_directory(args.organs)
    if not reports:
        # Not a pass. An empty registry means the glob found nothing, which is far more often
        # a wrong path than a deliberate state.
        print(f"FAIL  no */manifest.yaml found under {args.organs}", file=sys.stderr)
        return 1

    invalid = 0
    for report in reports:
        status = "PASS" if report.is_valid else "FAIL"
        print(f"{status}  {report.organ or '<unnamed>'}  ({report.path.relative_to(REPO_ROOT)})")
        for issue in report.errors:
            print(f"        {issue}")
        for issue in report.deferred:
            print(f"        {issue}")
        invalid += not report.is_valid

    total = len(reports)
    print(f"\n  {total - invalid} of {total} manifests valid")
    if invalid:
        print("  A manifest that fails validation excludes its organ. It is never silently skipped.")
    return 1 if invalid else 0


if __name__ == "__main__":
    raise SystemExit(main())
