"""Corporea-Brain evaluation harness.

A shipped component with its own tests, not a notebook. Specified by
``docs/10-EVALUATION_PROTOCOL.md``.

Architectural seam 4: **this package never imports the application.** It runs against CLI
modules and file artifacts so that every number in the results chapter can be reproduced
without a GUI. The seam is asserted mechanically by
``eval/tests/test_seam_no_application_import.py`` rather than left to reviewer vigilance.
"""

__all__ = ["metrics", "aggregate"]
