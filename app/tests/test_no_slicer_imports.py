"""``corporea_core`` imports no Slicer at import time.

``docs/14-CODING_STANDARDS.md``: a scripted module's logic lives in a plain class with no
Slicer imports at module import time, and the widget is a thin shell over it. **This one rule
is what makes the module testable at all.** ``docs/16``: enforce it and the unit layer is
easy; break it and the layer is impossible.

It will be broken by accident, not by intent. Someone will need a transform, ``vtk`` has a
good one, and the import will look entirely reasonable in review.
"""

from __future__ import annotations

import importlib
import pkgutil

import corporea_core
import pytest

pytestmark = pytest.mark.seam

FORBIDDEN = ("slicer", "vtk", "ctk", "qt", "PythonQt")


def core_module_names() -> list[str]:
    return [module.name for module in pkgutil.iter_modules(corporea_core.__path__)]


@pytest.mark.parametrize("module_name", core_module_names())
def test_module_imports_without_slicer_on_the_path(module_name: str) -> None:
    # Nothing installs slicer, vtk, ctk or qt into the pipeline venv, so a module that
    # imported one would fail here with ImportError. That failure is the assertion.
    importlib.import_module(f"corporea_core.{module_name}")


@pytest.mark.parametrize("module_name", core_module_names())
def test_module_source_names_no_slicer_import(module_name: str) -> None:
    """Also read the source, so the rule holds on a machine that does have Slicer installed.

    The import test above passes for the wrong reason inside Slicer's own interpreter, where
    every forbidden name resolves. Developers do run tests there.
    """
    module = importlib.import_module(f"corporea_core.{module_name}")
    source = open(module.__file__, encoding="utf-8").read()  # noqa: SIM115
    for name in FORBIDDEN:
        assert f"import {name}\n" not in source, (
            f"corporea_core.{module_name} imports {name} at module level. Move the logic that "
            f"needs it into the widget shell, which is allowed to."
        )
        assert f"from {name} import" not in source, (
            f"corporea_core.{module_name} imports from {name} at module level."
        )
