"""BrainTwin Desktop offline imaging pipeline.

Runs outside Slicer, in its own Python 3.12 environment. Nothing in this package imports
``slicer``, ``vtk``, ``ctk`` or ``qt``, which is what makes the unit test layer in
``pipeline/tests`` fast and headless.

Specified by ``docs/06-IMAGING_PIPELINE.md``.
"""

__all__ = ["orientation", "phantom"]
