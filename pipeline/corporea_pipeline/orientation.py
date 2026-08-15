"""Anatomical orientation: the assertion that stops a left/right flip reaching a result.

Read ``docs/06-IMAGING_PIPELINE.md``, the orientation section, before changing anything here.
It describes the single failure mode most likely to invalidate the entire project, and it is
invisible when it happens: a flip anywhere in the chain puts the lesion in the wrong
hemisphere, and attribution, tract involvement, deficit hypotheses and the eloquent-proximity
warning are then all confidently, plausibly wrong. The images look fine.

The one idea this module exists to encode
----------------------------------------
**The assertion is made in world space, never in voxel space.**

Flipping an array *and* flipping its affine to match is not a bug. It is the same physical
object written down in a different order, and every correct reorientation does exactly that.
The bug is when the array and the affine stop agreeing. A voxel-index assertion cannot tell
those two apart: it fails on the correct case and passes on a resample that silently dropped
the affine update. So every check here goes through the affine and lands on an anatomical
side.

Coordinate convention, and why it does not touch ADR-006
--------------------------------------------------------
The NIfTI standard defines a volume's affine as mapping voxel indices to **RAS+**
millimetres: +x toward the patient's right, +y anterior, +z superior. That is the file
format's own definition, not a choice this project makes, so relying on it here does not
pre-empt `ADR-006 <../../docs/DECISIONS/ADR-006-coordinate-space-and-atlas.md>`_, which
selects the canonical *space and atlas* and is still open. Nothing in this module names a
template, a parcellation or a coordinate space, per architectural seam 5.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

import numpy as np
from nibabel.orientations import aff2axcodes

__all__ = [
    "Axis",
    "Pole",
    "WorldPoint",
    "MarkerCheck",
    "OrientationReport",
    "OrientationError",
    "voxel_to_world",
    "mask_centre_of_world",
    "axis_codes",
    "determinant_sign",
    "voxel_sizes_mm",
    "pole_of",
    "check_marker",
    "assert_no_flip",
]

# Below this, a coordinate is not meaningfully on either side of the plane and saying which
# would be a guess. Callers working at finer scales pass their own.
DEFAULT_TOLERANCE_MM: Final[float] = 1.0


class Axis(Enum):
    """An anatomical axis, as the two poles it runs between plus its neutral plane.

    Ordered to match NIfTI RAS+, so ``Axis.LEFT_RIGHT.index`` is the x column of the affine.
    """

    LEFT_RIGHT = (0, "left", "right", "midline")
    POSTERIOR_ANTERIOR = (1, "posterior", "anterior", "mid-coronal")
    INFERIOR_SUPERIOR = (2, "inferior", "superior", "mid-axial")

    def __init__(self, index: int, negative: str, positive: str, neutral: str) -> None:
        self.index = index
        self.negative = negative
        self.positive = positive
        self.neutral = neutral


class Pole(Enum):
    """Where something sits on an anatomical axis.

    The neutral members are not a convenience. A structure on the midline is a third answer,
    and forcing it into ``LEFT`` or ``RIGHT`` because the sign bit happened to fall one way
    is precisely the silent guess this module exists to prevent.
    """

    LEFT = "left"
    RIGHT = "right"
    MIDLINE = "midline"

    POSTERIOR = "posterior"
    ANTERIOR = "anterior"
    MID_CORONAL = "mid-coronal"

    INFERIOR = "inferior"
    SUPERIOR = "superior"
    MID_AXIAL = "mid-axial"


class OrientationError(AssertionError):
    """A geometry stage produced a volume whose anatomy is not where it must be.

    Deliberately an ``AssertionError``: this is never caught and handled. A pipeline that
    reaches this state has no valid output and must stop.
    """


@dataclass(frozen=True)
class WorldPoint:
    """A point in NIfTI RAS+ millimetres."""

    x: float
    y: float
    z: float

    def component(self, axis: Axis) -> float:
        """The signed millimetre coordinate along ``axis``."""
        return (self.x, self.y, self.z)[axis.index]

    def as_tuple(self) -> tuple[float, float, float]:
        return (self.x, self.y, self.z)


@dataclass(frozen=True)
class MarkerCheck:
    """One marker's verdict, in the shape the QC report and the log both need.

    Carries the observed value whether it passed or failed. A check that reports only
    ``False`` sends the reader back to the data to find out what happened, and at three in
    the morning they will not.
    """

    label: str
    axis: Axis
    expected: Pole
    observed: Pole
    centre: WorldPoint
    voxel_count: int
    tolerance_mm: float

    @property
    def passed(self) -> bool:
        return self.observed is self.expected

    def describe(self) -> str:
        verdict = "ok" if self.passed else "FLIPPED"
        return (
            f"{verdict}: marker {self.label!r} expected {self.expected.value}, "
            f"observed {self.observed.value} at RAS "
            f"({self.centre.x:+.2f}, {self.centre.y:+.2f}, {self.centre.z:+.2f}) mm "
            f"from {self.voxel_count} voxels, tolerance {self.tolerance_mm} mm"
        )


@dataclass(frozen=True)
class OrientationReport:
    """The orientation panel of a per-case QC report.

    Contents are those ``docs/06`` requires of that panel: the orientation code, the affine
    determinant sign, and the per-marker verdicts. The rendered image with laterality burned
    in is produced by the report writer from this object.
    """

    axis_codes: tuple[str, str, str]
    determinant_sign: int
    voxel_sizes_mm: tuple[float, float, float]
    checks: tuple[MarkerCheck, ...]

    @property
    def passed(self) -> bool:
        return all(check.passed for check in self.checks)

    @property
    def failures(self) -> tuple[MarkerCheck, ...]:
        return tuple(check for check in self.checks if not check.passed)

    def describe(self) -> str:
        header = (
            f"orientation code {''.join(self.axis_codes)}, "
            f"determinant sign {self.determinant_sign:+d}, "
            f"voxel size {self.voxel_sizes_mm} mm"
        )
        return "\n".join([header, *(check.describe() for check in self.checks)])


def voxel_to_world(affine: np.ndarray, ijk: tuple[float, float, float]) -> WorldPoint:
    """Map a voxel index to RAS+ millimetres through ``affine``.

    Accepts fractional indices, because a centre of mass rarely lands on an integer.
    """
    _validate_affine(affine)
    homogeneous = np.asarray([*ijk, 1.0], dtype=np.float64)
    x, y, z = (np.asarray(affine, dtype=np.float64) @ homogeneous)[:3]
    return WorldPoint(float(x), float(y), float(z))


def mask_centre_of_world(mask: np.ndarray, affine: np.ndarray) -> WorldPoint:
    """The centre of mass of a boolean mask, in RAS+ millimetres.

    Unweighted by intensity on purpose: for a uniform marker the answer is then a plain mean
    of voxel indices, which is hand-computable, and a known-answer test that cannot be worked
    out by hand is not a known-answer test.

    Raises ``OrientationError`` when the mask is empty. There is no centre of nothing, and
    returning the volume origin, or a zero, would read downstream as a real measurement.
    """
    indices = np.argwhere(np.asarray(mask, dtype=bool))
    if indices.size == 0:
        raise OrientationError(
            "empty mask has no centre of mass. A marker that vanished is a geometry failure, "
            "not a zero."
        )
    return voxel_to_world(affine, tuple(indices.mean(axis=0)))


def axis_codes(affine: np.ndarray) -> tuple[str, str, str]:
    """The three-letter orientation code of ``affine``, for example ``('R', 'A', 'S')``."""
    _validate_affine(affine)
    return tuple(aff2axcodes(np.asarray(affine, dtype=np.float64)))


def determinant_sign(affine: np.ndarray) -> int:
    """Sign of the direction-matrix determinant: ``+1`` right-handed, ``-1`` left-handed.

    Goes in the QC panel because a *change* of sign across a stage is the fingerprint of a
    flip that was applied to the data without being applied to the affine.

    Raises ``OrientationError`` on a singular direction matrix, which is a degenerate volume
    and not something to report a sign for.
    """
    _validate_affine(affine)
    determinant = float(np.linalg.det(np.asarray(affine, dtype=np.float64)[:3, :3]))
    if determinant == 0.0:
        raise OrientationError(
            "affine direction matrix is singular; the volume has no well-defined handedness"
        )
    return 1 if determinant > 0.0 else -1


def voxel_sizes_mm(affine: np.ndarray) -> tuple[float, float, float]:
    """Millimetre spacing along each voxel axis, as the column norms of the affine."""
    _validate_affine(affine)
    sizes = np.linalg.norm(np.asarray(affine, dtype=np.float64)[:3, :3], axis=0)
    return (float(sizes[0]), float(sizes[1]), float(sizes[2]))


def pole_of(
    point: WorldPoint,
    axis: Axis,
    tolerance_mm: float = DEFAULT_TOLERANCE_MM,
) -> Pole:
    """Which pole of ``axis`` ``point`` sits on, or the neutral plane within tolerance."""
    if tolerance_mm < 0.0:
        raise ValueError(f"tolerance_mm must not be negative, got {tolerance_mm}")
    value = point.component(axis)
    if abs(value) <= tolerance_mm:
        return Pole(axis.neutral)
    return Pole(axis.positive) if value > 0.0 else Pole(axis.negative)


def check_marker(
    volume: np.ndarray,
    affine: np.ndarray,
    *,
    label: str,
    intensity: int,
    axis: Axis,
    expected: Pole,
    tolerance_mm: float = DEFAULT_TOLERANCE_MM,
) -> MarkerCheck:
    """Locate the marker written at ``intensity`` and report which pole of ``axis`` it is on.

    The marker is found by exact intensity match, so the phantom gives every marker a unique
    value. Connected-component labelling would be more general and would also introduce a
    second thing that can be wrong inside the one test the project cannot afford to have
    quietly broken.

    Raises ``OrientationError`` if no voxel carries ``intensity``: a marker that disappeared
    is a geometry failure in its own right, and reporting it as "not on the expected side"
    would name the wrong cause.
    """
    if expected.value not in (axis.negative, axis.positive, axis.neutral):
        raise ValueError(f"{expected.value!r} is not a pole of {axis.name}")

    mask = np.asarray(volume) == intensity
    voxel_count = int(mask.sum())
    if voxel_count == 0:
        raise OrientationError(
            f"marker {label!r} (intensity {intensity}) is absent from the volume. It was not "
            f"moved to the wrong side, it is gone: check the stage that resampled or "
            f"interpolated it."
        )

    centre = mask_centre_of_world(mask, affine)
    return MarkerCheck(
        label=label,
        axis=axis,
        expected=expected,
        observed=pole_of(centre, axis, tolerance_mm),
        centre=centre,
        voxel_count=voxel_count,
        tolerance_mm=tolerance_mm,
    )


def assert_no_flip(report: OrientationReport) -> OrientationReport:
    """Raise ``OrientationError`` if any marker is on the wrong side.

    Returns the report on success so it can be logged and attached to the QC panel in one
    expression. The report is produced whether or not it passes, because the failure detail
    is what makes the failure diagnosable.
    """
    if report.passed:
        return report
    raise OrientationError(
        "orientation assertion failed. Every downstream output from this volume would be in "
        "the wrong hemisphere and would look entirely normal.\n" + report.describe()
    )


def _validate_affine(affine: np.ndarray) -> None:
    array = np.asarray(affine)
    if array.shape != (4, 4):
        raise ValueError(f"affine must be 4x4, got shape {array.shape}")
    if not np.all(np.isfinite(array)):
        raise ValueError("affine contains non-finite values")
