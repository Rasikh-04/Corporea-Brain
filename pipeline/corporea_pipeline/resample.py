"""Pipeline stage 3: reorientation and resampling, with the geometry asserted on the way out.

``docs/06-IMAGING_PIPELINE.md``, stage 3: "Reorient to ``<CANONICAL_SPACE>`` orientation.
Resample to a declared isotropic grid. Record the original orientation code and the affine
before and after." And then, in the same section: **this is where the project lives or dies.**

Reorientation was already built, in ``phantom.py``, because the orientation assertion needed
it before anything else existed. This module is the other half — the resample — plus the
stage entry point that runs both and refuses to return a volume whose anatomy has moved.

Why the resample is the dangerous half
--------------------------------------
Reorientation permutes and flips voxel axes. It is exactly reversible, it moves no anatomy,
and every marker keeps its voxel count. Resampling does none of those things: it lands the
data on a new grid, so **voxel counts change, boundaries move by up to half a voxel, and
small structures can vanish outright.** That is not a defect to fix, it is what resampling
is. What matters is that the world coordinates survive it, and that is what this module
asserts rather than assumes.

The invariant, stated once
--------------------------
A resample is correct when **every physical point keeps its millimetre coordinate.** The
array changes shape, the affine changes scale, and the composition of the two is unchanged.
So the output affine here is not adjusted by hand; it is constructed from the input
direction cosines and the requested spacing, and the sampling grid is then derived *from
that affine* by mapping each output voxel back through world space into input voxel indices.
There is no second place where the two could be made to disagree.

``<CANONICAL_SPACE>`` stays a placeholder
-----------------------------------------
`ADR-006 <../../docs/DECISIONS/ADR-006-coordinate-space-and-atlas.md>`_ is open, so this
module names no space, no template and no atlas. The target orientation code and the target
spacing are **parameters with no defaults**. When ADR-006 closes, one caller gains two
constants; nothing here changes. Architectural seam 5.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any, Final

import numpy as np
from scipy.ndimage import affine_transform

from . import __version__
from .orientation import (
    OrientationError,
    OrientationReport,
    WorldPoint,
    axis_codes,
    determinant_sign,
    voxel_sizes_mm,
)
from .phantom import PhantomMarker, orientation_report, reorient

__all__ = [
    "Interpolation",
    "ResampleError",
    "Stage3Record",
    "Stage3Result",
    "TOOL_NAME",
    "output_grid",
    "resample_to_grid",
    "run_stage3",
    "world_bounding_box",
]

TOOL_NAME: Final[str] = "corporea_pipeline.resample"

# How far a world coordinate may move across the stage before it is called a failure rather
# than a resampling artifact. One output voxel diagonal is the honest bound: a point that
# lands in the correct output voxel cannot be located more precisely than that, and anything
# larger than it is not interpolation, it is a geometry error.
CORNER_TOLERANCE_VOXELS: Final[float] = 1.0


class Interpolation(StrEnum):
    """How to sample the input grid. There is deliberately no default.

    ``NEAREST`` is the only correct choice for a label map, a parcellation or a lesion mask.
    ``LINEAR`` averages neighbouring voxels, and the average of label 3 and label 7 is label
    5, which is a different structure. The wrong choice here produces a volume that looks
    entirely normal and whose region boundaries are fiction, so the caller states it every
    time rather than inheriting it from a default nobody re-reads.
    """

    NEAREST = "nearest"
    LINEAR = "linear"

    @property
    def spline_order(self) -> int:
        """The ``scipy.ndimage`` order this corresponds to."""
        return 0 if self is Interpolation.NEAREST else 1


class ResampleError(ValueError):
    """The requested resample is not something that can be done correctly."""


@dataclass(frozen=True)
class Stage3Record:
    """Provenance for one stage 3 run, in primitives only, ready to serialise.

    Rule 6: source series, tool, version, parameters, timestamp, on every derived artifact.
    ``docs/06`` adds the specific requirement for this stage — the original orientation code
    and the affine before and after — because those two are what a later reader needs to
    reconstruct what happened, and neither is recoverable from the output alone.

    Primitives rather than arrays on purpose. This object is written to a sidecar next to the
    volume, and a record that needs numpy to read is a record that will not be read.
    """

    tool: str
    tool_version: str
    timestamp_utc: str
    interpolation: str
    source_axis_codes: str
    target_axis_codes: str
    source_shape: tuple[int, int, int]
    target_shape: tuple[int, int, int]
    source_spacing_mm: tuple[float, float, float]
    target_spacing_mm: tuple[float, float, float]
    source_affine: tuple[tuple[float, ...], ...]
    target_affine: tuple[tuple[float, ...], ...]
    source_determinant_sign: int
    target_determinant_sign: int

    def as_dict(self) -> dict[str, Any]:
        """A JSON-serialisable mapping, for the provenance sidecar."""
        return {
            "tool": self.tool,
            "tool_version": self.tool_version,
            "timestamp_utc": self.timestamp_utc,
            "interpolation": self.interpolation,
            "source": {
                "axis_codes": self.source_axis_codes,
                "shape": list(self.source_shape),
                "spacing_mm": list(self.source_spacing_mm),
                "affine": [list(row) for row in self.source_affine],
                "determinant_sign": self.source_determinant_sign,
            },
            "target": {
                "axis_codes": self.target_axis_codes,
                "shape": list(self.target_shape),
                "spacing_mm": list(self.target_spacing_mm),
                "affine": [list(row) for row in self.target_affine],
                "determinant_sign": self.target_determinant_sign,
            },
        }

    def describe(self) -> str:
        return (
            f"stage 3 {self.interpolation}: "
            f"{self.source_axis_codes} {self.source_shape} @ {self.source_spacing_mm} mm "
            f"-> {self.target_axis_codes} {self.target_shape} @ {self.target_spacing_mm} mm "
            f"({self.tool} {self.tool_version}, {self.timestamp_utc})"
        )


@dataclass(frozen=True)
class Stage3Result:
    """The output volume, its affine, its provenance, and the geometry check that cleared it.

    ``orientation`` is ``None`` when the caller supplied no markers, which is the ordinary
    case for patient data: there is nothing in a real head whose laterality is known a priori
    to assert against. The marker-free path is not unchecked — the world bounding box and the
    determinant sign are verified either way — but it is a weaker check than the phantom's,
    and a ``None`` here says so rather than implying an assertion that was never made.
    """

    data: np.ndarray
    affine: np.ndarray
    record: Stage3Record
    orientation: OrientationReport | None


def world_bounding_box(
    shape: tuple[int, int, int],
    affine: np.ndarray,
) -> tuple[WorldPoint, WorldPoint]:
    """The axis-aligned RAS+ millimetre box spanned by the eight corner voxel centres.

    Computed over all eight corners rather than two, because under a rotated or flipped
    affine the minimum and maximum along a world axis need not come from opposite corners of
    the voxel array.
    """
    _validate_shape(shape)
    corners = np.array(
        [
            [i, j, k, 1.0]
            for i in (0, shape[0] - 1)
            for j in (0, shape[1] - 1)
            for k in (0, shape[2] - 1)
        ],
        dtype=np.float64,
    )
    world = (np.asarray(affine, dtype=np.float64) @ corners.T)[:3]
    low = world.min(axis=1)
    high = world.max(axis=1)
    return (
        WorldPoint(float(low[0]), float(low[1]), float(low[2])),
        WorldPoint(float(high[0]), float(high[1]), float(high[2])),
    )


def output_grid(
    shape: tuple[int, int, int],
    affine: np.ndarray,
    spacing_mm: tuple[float, float, float],
) -> tuple[tuple[int, int, int], np.ndarray]:
    """The shape and affine of the resampled grid, before any voxel is touched.

    Separated from the sampling so it can be checked on its own, and so a caller can ask what
    a resample would cost in memory before paying for it.

    Two decisions are fixed here, and both are chosen to be the ones with no hidden
    arithmetic:

    - **The origin does not move.** Output voxel ``(0, 0, 0)`` sits at the same world point as
      input voxel ``(0, 0, 0)``. Re-centring the field of view instead would be defensible,
      but it puts a second translation into the affine that has to be got right, and getting
      it wrong shifts everything downstream by a constant nobody sees.
    - **The field of view is covered, never cropped.** The extent along each voxel axis is
      rounded up, so the output spans at least the input. Rounding down would silently drop a
      slice, and the slice it drops is at the edge, where a peripheral lesion lives.

    Direction cosines are carried over unchanged: this function changes scale, not
    orientation. Reorientation is ``phantom.reorient`` and it runs first.
    """
    _validate_shape(shape)
    _validate_spacing(spacing_mm)
    source = np.asarray(affine, dtype=np.float64)
    _validate_affine_for_resample(source)

    source_spacing = voxel_sizes_mm(source)
    directions = source[:3, :3] / np.asarray(source_spacing, dtype=np.float64)

    target_shape = tuple(
        int(math.ceil((extent - 1) * old / new)) + 1
        for extent, old, new in zip(shape, source_spacing, spacing_mm, strict=True)
    )
    target = np.eye(4, dtype=np.float64)
    target[:3, :3] = directions * np.asarray(spacing_mm, dtype=np.float64)
    target[:3, 3] = source[:3, 3]
    return (target_shape[0], target_shape[1], target_shape[2]), target


def resample_to_grid(
    data: np.ndarray,
    affine: np.ndarray,
    *,
    spacing_mm: tuple[float, float, float],
    interpolation: Interpolation,
) -> tuple[np.ndarray, np.ndarray]:
    """Resample onto a grid of the requested spacing, preserving every world coordinate.

    The sampling transform is derived from the two affines and nothing else::

        world  = A_out @ p_out          (output index to millimetres)
        p_in   = A_in^-1 @ world        (millimetres to input index)
        p_in   = (A_in^-1 @ A_out) @ p_out

    so if the output affine is wrong the sampled data is wrong in the *same* way, and the two
    cannot drift apart into a volume that reads correctly and is not. This is the whole reason
    the affine is built first and the grid derived from it, rather than the array being
    zoomed and an affine written afterwards to match.

    Integer inputs come back as the same integer dtype. Under ``LINEAR`` the interpolated
    values are rounded to nearest rather than truncated toward zero, because truncation biases
    every voxel in the volume downward by up to one unit and that bias survives into any
    intensity-derived measurement.
    """
    array = np.asarray(data)
    if array.ndim != 3:
        raise ResampleError(
            f"stage 3 resamples a 3D volume, got shape {array.shape}. A 4D series is split "
            f"into volumes upstream, at stage 1."
        )
    shape = (int(array.shape[0]), int(array.shape[1]), int(array.shape[2]))
    source = np.asarray(affine, dtype=np.float64)
    target_shape, target_affine = output_grid(shape, source, spacing_mm)

    # inv(A_in) @ A_out, split into the 3x3 the sampler applies and the offset it adds.
    combined = np.linalg.inv(source) @ target_affine
    matrix = combined[:3, :3]
    offset = combined[:3, 3]

    sampled = affine_transform(
        array.astype(np.float64, copy=False),
        matrix=matrix,
        offset=offset,
        output_shape=target_shape,
        order=interpolation.spline_order,
        mode="constant",
        cval=0.0,
        prefilter=False,
    )
    if np.issubdtype(array.dtype, np.integer):
        sampled = np.rint(sampled)
    return sampled.astype(array.dtype, copy=False), target_affine


def run_stage3(
    data: np.ndarray,
    affine: np.ndarray,
    *,
    target_axis_codes: tuple[str, str, str],
    spacing_mm: tuple[float, float, float],
    interpolation: Interpolation,
    markers: tuple[PhantomMarker, ...] | None = None,
    tolerance_mm: float = 1.0,
) -> Stage3Result:
    """Reorient, resample, and refuse to return anything whose geometry moved.

    Order is reorient first, resample second. The reverse also works, but reorienting first
    means the resample runs on axes that are already in the target order, so ``spacing_mm[0]``
    means the spacing along the target's first axis in both the request and the result. With
    the other order it would mean the spacing along whichever axis the scanner happened to
    write first, and that is a parameter whose meaning depends on the input file.

    Three things are checked before the result is handed back:

    1. **The resample does not change the affine's handedness.** Note where that check sits:
       across the *resample*, not across the stage. Reorientation changes handedness whenever
       the target code has the opposite handedness to the source — ``RAS`` is right-handed and
       ``LAS`` is left-handed, and rewriting one as the other is the ordinary, correct thing
       stage 3 is for. Asserting the sign across the whole stage would therefore fire on every
       correct run, and an assertion that fires on correct runs is one somebody disables. The
       resample only scales, so across *it* the sign is invariant, and a change there is the
       fingerprint of a flip introduced by the sampler.
    2. **The world bounding box is preserved**, within one output voxel diagonal. This is the
       marker-free check. It catches an affine that was not updated to match a grid that was —
       the classic dropped-affine resample — because the old affine over the new shape spans
       the wrong extent. It does **not** catch data flipped with its affine left intact: that
       one moves no world coordinate the shape can see, and only a marker finds it.
    3. **Every supplied marker is still on its anatomical side**, and its centre of mass has
       not moved more than ``tolerance_mm``. This is the strong check, and it is the one that
       catches the case (2) cannot. It runs on the phantom in CI on every commit.

    Passing ``markers`` for patient data is meaningless and is not supported: markers are
    located by exact intensity, which only the phantom guarantees. That is exactly why the
    phantom exists — there is nothing in a real head whose laterality is known a priori, so
    the assertion is made once, on a volume whose answer is known, on every commit.
    """
    array = np.asarray(data)
    source = np.asarray(affine, dtype=np.float64)
    source_shape = (int(array.shape[0]), int(array.shape[1]), int(array.shape[2]))
    source_codes = axis_codes(source)
    source_sign = determinant_sign(source)
    source_box = world_bounding_box(source_shape, source)

    oriented, oriented_affine = reorient(array, source, target_axis_codes)
    oriented_sign = determinant_sign(oriented_affine)
    resampled, target_affine = resample_to_grid(
        oriented,
        oriented_affine,
        spacing_mm=spacing_mm,
        interpolation=interpolation,
    )
    target_shape = (
        int(resampled.shape[0]),
        int(resampled.shape[1]),
        int(resampled.shape[2]),
    )

    target_sign = determinant_sign(target_affine)
    if target_sign != oriented_sign:
        raise OrientationError(
            f"the resample changed the affine's handedness, {oriented_sign:+d} to "
            f"{target_sign:+d}. Resampling only rescales the grid, so the sign cannot move: "
            f"this is an array flipped by the sampler, and every downstream result would be "
            f"mirrored and would look entirely normal."
        )

    _assert_bounding_box_preserved(source_box, target_shape, target_affine, spacing_mm)

    report: OrientationReport | None = None
    if markers is not None:
        report = orientation_report(resampled, target_affine, markers, tolerance_mm)
        _assert_markers_did_not_move(report, markers, tolerance_mm)

    record = Stage3Record(
        tool=TOOL_NAME,
        tool_version=__version__,
        timestamp_utc=datetime.now(UTC).isoformat(timespec="seconds"),
        interpolation=str(interpolation),
        source_axis_codes="".join(source_codes),
        target_axis_codes="".join(axis_codes(target_affine)),
        source_shape=source_shape,
        target_shape=target_shape,
        source_spacing_mm=voxel_sizes_mm(source),
        target_spacing_mm=voxel_sizes_mm(target_affine),
        source_affine=_as_rows(source),
        target_affine=_as_rows(target_affine),
        source_determinant_sign=source_sign,
        target_determinant_sign=target_sign,
    )
    return Stage3Result(
        data=resampled,
        affine=target_affine,
        record=record,
        orientation=report,
    )


def _assert_bounding_box_preserved(
    source_box: tuple[WorldPoint, WorldPoint],
    target_shape: tuple[int, int, int],
    target_affine: np.ndarray,
    spacing_mm: tuple[float, float, float],
) -> None:
    """The output must span the input's world extent, to within one output voxel diagonal.

    Stated as a tolerance rather than an equality because it cannot be an equality: the output
    grid covers the input extent and rounds up, so its far corner sits up to one voxel beyond.
    The bound that matters is that neither corner is *inside* the input box by more than a
    voxel, which is how a lost slice or a mis-signed origin shows up.
    """
    tolerance = CORNER_TOLERANCE_VOXELS * float(np.linalg.norm(np.asarray(spacing_mm)))
    target_box = world_bounding_box(target_shape, target_affine)
    for name, source_corner, target_corner in (
        ("lower", source_box[0], target_box[0]),
        ("upper", source_box[1], target_box[1]),
    ):
        drift = np.abs(np.asarray(target_corner.as_tuple()) - np.asarray(source_corner.as_tuple()))
        if float(drift.max()) > tolerance:
            raise OrientationError(
                f"stage 3 moved the {name} corner of the field of view from "
                f"{source_corner.as_tuple()} to {target_corner.as_tuple()} mm, a drift of "
                f"{float(drift.max()):.3f} mm against a tolerance of {tolerance:.3f} mm. "
                f"The array and the affine no longer describe the same physical object."
            )


def _assert_markers_did_not_move(
    report: OrientationReport,
    markers: tuple[PhantomMarker, ...],
    tolerance_mm: float,
) -> None:
    """Every marker on its expected side, and within ``tolerance_mm`` of where it started.

    The side check alone is necessary and not sufficient. A resample that shifted the whole
    volume by 20 mm along x leaves every marker on the side it started, and would pass a
    laterality-only check while being badly wrong.

    Reports all offenders before raising, per rule 4.
    """
    expected_by_label = {marker.label: marker.expected_centre_mm for marker in markers}
    drifted: list[str] = []
    for check in report.checks:
        expected_centre = expected_by_label.get(check.label)
        if expected_centre is None:
            continue
        drift = float(
            np.linalg.norm(
                np.asarray(check.centre.as_tuple()) - np.asarray(expected_centre.as_tuple())
            )
        )
        if drift > tolerance_mm:
            drifted.append(
                f"  {check.label!r} centre moved {drift:.3f} mm, from "
                f"{expected_centre.as_tuple()} to {check.centre.as_tuple()} mm"
            )
    if drifted:
        raise OrientationError(
            "stage 3 moved marker anatomy in world space, tolerance "
            f"{tolerance_mm} mm:\n" + "\n".join(drifted)
        )
    if not report.passed:
        raise OrientationError(
            "stage 3 output failed the orientation assertion.\n" + report.describe()
        )


def _as_rows(affine: np.ndarray) -> tuple[tuple[float, ...], ...]:
    return tuple(tuple(float(value) for value in row) for row in np.asarray(affine))


def _validate_shape(shape: tuple[int, int, int]) -> None:
    if len(shape) != 3 or any(extent < 1 for extent in shape):
        raise ResampleError(f"shape must be three positive extents, got {shape}")


def _validate_spacing(spacing_mm: tuple[float, float, float]) -> None:
    if len(spacing_mm) != 3:
        raise ResampleError(f"spacing_mm must have three components, got {spacing_mm}")
    for value in spacing_mm:
        if not math.isfinite(value) or value <= 0.0:
            raise ResampleError(
                f"spacing_mm must be positive and finite, got {spacing_mm}. A zero or "
                f"negative spacing produces a singular affine and an unbounded output grid."
            )


def _validate_affine_for_resample(affine: np.ndarray) -> None:
    if affine.shape != (4, 4):
        raise ResampleError(f"affine must be 4x4, got shape {affine.shape}")
    if not np.all(np.isfinite(affine)):
        raise ResampleError("affine contains non-finite values")
    if float(np.linalg.det(affine[:3, :3])) == 0.0:
        raise ResampleError(
            "affine direction matrix is singular: the volume has zero extent along at least "
            "one axis and cannot be resampled onto a physical grid."
        )
