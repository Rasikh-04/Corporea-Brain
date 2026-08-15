"""Architectural seam 4, asserted mechanically.

> The evaluation harness never imports the application. It runs against CLI modules and file
> artifacts, so results can be reproduced without a GUI.

``docs/03-ARCHITECTURE.md``, seams. ``docs/10`` states the consequence: every number in the
results chapter must be reproducible headless, by someone who has not built the application.

A seam kept by reviewer vigilance is a seam that survives until the week somebody is busy. The
import that breaks this one will not look like a violation. It will look like reusing a
perfectly good function.

Run in a subprocess because ``sys.modules`` is process-wide: another test in the same session
may legitimately have imported the application already, and this check must not be able to
pass or fail on test ordering.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

pytestmark = pytest.mark.seam

REPO_ROOT = Path(__file__).resolve().parents[2]

# Import machinery, not the application. Everything else under these names is forbidden.
FORBIDDEN_PREFIXES = ("slicer", "vtk", "ctk", "qt", "PythonQt", "braintwin_core")

# Substituted with str.replace rather than str.format, because the probe itself contains
# braces that format would try to interpret.
PROBE = """
import importlib
import pkgutil
import sys

__IMPORTS__

for module in pkgutil.iter_modules(braintwin_eval.__path__):
    importlib.import_module("braintwin_eval." + module.name)

forbidden = __FORBIDDEN__
leaked = sorted(
    name
    for name in sys.modules
    if any(name == p or name.startswith(p + ".") for p in forbidden)
)
print("\\n".join(leaked))
"""


def probe_source(imports: str) -> str:
    return PROBE.replace("__IMPORTS__", imports).replace(
        "__FORBIDDEN__", repr(FORBIDDEN_PREFIXES)
    )


def run_probe(imports: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-c", probe_source(imports)],
        cwd=REPO_ROOT,
        env={"PYTHONPATH": f"{REPO_ROOT / 'eval'}:{REPO_ROOT / 'app'}"},
        capture_output=True,
        text=True,
    )


def test_importing_the_harness_pulls_in_no_part_of_the_application() -> None:
    completed = run_probe("import braintwin_eval")
    assert completed.returncode == 0, completed.stderr

    leaked = [line for line in completed.stdout.splitlines() if line.strip()]
    assert not leaked, (
        "seam 4 is broken. Importing braintwin_eval pulled in: "
        + ", ".join(leaked)
        + ". The harness must run against file artifacts and CLI modules only, so that the "
        "results chapter can be reproduced by someone who has not built the application."
    )


def test_the_probe_would_notice_a_violation() -> None:
    """The seam test above passes trivially if the probe is broken. This checks the probe.

    Imports a module that is genuinely on the path and genuinely forbidden, and asserts the
    same machinery reports it. Without this, a typo in ``FORBIDDEN_PREFIXES`` would leave a
    green test guarding nothing.
    """
    completed = run_probe("import braintwin_eval, braintwin_core")
    assert completed.returncode == 0, completed.stderr
    assert "braintwin_core" in completed.stdout
