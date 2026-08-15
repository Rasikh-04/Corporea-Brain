"""Pure Python shared between Slicer modules and headless tooling.

``docs/14-CODING_STANDARDS.md``: a scripted module's logic lives in a plain class with no
Slicer imports at module import time, and the widget is a thin shell over it. That one rule is
what makes the unit test layer possible at all. This package is where that logic goes when it
is also needed outside Slicer, such as by a CI script.

**Nothing here imports ``slicer``, ``vtk``, ``ctk``, ``qt`` or ``PythonQt`` at import time.**
Asserted by ``app/tests/test_no_slicer_imports.py``, not left to reviewer vigilance.
"""

__all__ = ["organ_manifest"]
