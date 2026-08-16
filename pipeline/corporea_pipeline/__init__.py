"""Corporea-Brain offline imaging pipeline.

Runs outside Slicer, in its own Python 3.12 environment. Nothing in this package imports
``slicer``, ``vtk``, ``ctk`` or ``qt``, which is what makes the unit test layer in
``pipeline/tests`` fast and headless.

Specified by ``docs/06-IMAGING_PIPELINE.md``.
"""

# Stamped onto every derived artifact this package produces, per rule 6: no provenance, no
# results chapter. Hand-maintained and deliberately so — it changes when the pipeline's
# output changes, which is a judgement, not something a commit count can decide.
__version__ = "0.1.0"

__all__ = ["orientation", "phantom", "phi", "resample", "__version__"]
