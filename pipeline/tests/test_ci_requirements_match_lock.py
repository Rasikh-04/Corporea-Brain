"""The commit gate's dependency set must agree with the lock file.

``pipeline/requirements-ci.txt`` exists because the gate has to stay fast, per
``docs/16-TESTING_STRATEGY.md#ci``. The cost of a second pin list is that it can drift from
``requirements.lock.txt``, and the failure is quiet: CI goes green against one numpy while
every local run and every result in the thesis came from another.

``docs/15-BUILD_AND_ENVIRONMENT.md`` calls the lock the reproducibility artifact. This test is
what keeps that true when the gate does not install it.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.seam

PIPELINE_DIR = Path(__file__).resolve().parents[1]
CI_REQUIREMENTS = PIPELINE_DIR / "requirements-ci.txt"
LOCK = PIPELINE_DIR / "requirements.lock.txt"

# pip normalises distribution names for comparison: case-insensitive, and the three
# separators are equivalent. PyYAML in one file and pyyaml in the other is the same package.
_SEPARATORS = re.compile(r"[-_.]+")


def _normalise(name: str) -> str:
    return _SEPARATORS.sub("-", name).lower()


def _pins(path: Path) -> dict[str, str]:
    """Map normalised distribution name to pinned version, ignoring comments and blanks."""
    pins: dict[str, str] = {}
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        name, separator, version = line.partition("==")
        assert separator, f"{path.name}: {line!r} is not an exact pin, and every pin is exact"
        pins[_normalise(name)] = version.strip()
    return pins


def test_every_ci_pin_appears_in_the_lock_at_the_same_version() -> None:
    ci = _pins(CI_REQUIREMENTS)
    lock = _pins(LOCK)

    missing = sorted(name for name in ci if name not in lock)
    assert not missing, (
        f"{sorted(missing)} are pinned for CI but absent from requirements.lock.txt. "
        f"The gate would install something the pipeline environment does not have."
    )

    disagreements = {
        name: (version, lock[name]) for name, version in ci.items() if lock[name] != version
    }
    assert not disagreements, (
        f"CI and the lock disagree on {disagreements} (ci, lock). Regenerate the lock with "
        f"scripts/setup-env.sh, or correct requirements-ci.txt, but do not leave them differing: "
        f"a green gate would then be green against versions nobody runs."
    )


def test_the_ci_set_does_not_pull_torch() -> None:
    """The gate installs from PyPI alone, and the lock's `+cpu` torch is not published there.

    Beyond the resolution failure, torch is roughly a gigabyte the gate has no use for: no
    module under test imports it. If it ever legitimately belongs here, the workflow needs
    `--extra-index-url https://download.pytorch.org/whl/cpu` in the same change.
    """
    assert "torch" not in _pins(CI_REQUIREMENTS)
