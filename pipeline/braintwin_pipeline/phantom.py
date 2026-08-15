"""The synthetic asymmetric phantom, and the fixtures that prove the assertion can fail.

``docs/06-IMAGING_PIPELINE.md`` calls for a phantom "committed to the repository ... with an
unmistakable, deliberately lopsided marker", pushed through every stage that touches geometry.
This module is that phantom.

Why a generator and not a committed volume
------------------------------------------
The document says committed, and this deviates: the phantom is a deterministic function, and
``scripts/make_phantom.py`` writes it out on demand into a git-ignored path. Three reasons,
and the third is the one that matters.

1. ``.gitignore`` blocks every imaging extension under every path, and its own header says a
   pattern that occasionally ignores something harmless is correct while a gap that lets one
   DICOM through is not. Punching an exception through ``*.nii.gz`` for a fixture is exactly
   the gap that comment warns about, and rule 8 is not worth weakening for a file we can
   rebuild in a millisecond.
2. A generator is auditable. You can read what makes it lopsided. A committed binary is
   opaque, and a reviewer has to take its asymmetry on trust.
3. A committed fixture can go stale against the code that reads it and nothing says so. A
   generator cannot: there is one definition, so there is nothing to drift from.

There is no random number generator here and no seed. The phantom is pure geometry, so it is
bit-identical on every machine, which is what makes the expected centres below constants
rather than tolerances.

What the phantom is built to catch
----------------------------------
Three markers on three different anatomical poles: left, anterior, superior. Any single-axis
flip moves exactly one of them to the wrong pole. Any axis permutation moves markers between
axes. One marker would leave the other two axes unguarded, and a superior/inferior flip is
just as fatal to a result as a left/right one and attracts far less suspicion.

The grid is deliberately awkward, and each part of that is load-bearing:

- **Shape (64, 56, 48), all three different.** Equal dimensions let an axis transpose pass
  through silently because nothing about the array shape changes.
- **Spacing (1.0, 1.25, 2.0) mm, all three different.** Isotropic spacing hides the same bug
  in the affine: transpose the columns of an isotropic direction matrix and it is unchanged.
- **Origin (-28.0, -30.0, -40.0) mm, so the volume's centre is nowhere near the world
  origin.** A phantom whose middle sits at (0, 0, 0) is symmetric under negation of the
  affine's translation column, which is one of the ways a sign error hides.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

import numpy as np
from nibabel.orientations import (
    apply_orientation,
    axcodes2ornt,
    inv_ornt_aff,
    io_orientation,
    ornt_transform,
)

from .orientation import (
    Axis,
    MarkerCheck,
    OrientationReport,
    Pole,
    WorldPoint,
    axis_codes,
    check_marker,
    determinant_sign,
    voxel_sizes_mm,
)

__all__ = [
    "PhantomMarker",
    "Phantom",
    "PHANTOM_SHAPE",
    "PHANTOM_SPACING_MM",
    "PHANTOM_ORIGIN_MM",
    "PHANTOM_MARKERS",
    "BACKGROUND_INTENSITY",
    "build_phantom",
    "reorient",
    "break_orientation",
    "orientation_report",
]

PHANTOM_SHAPE: Final[tuple[int, int, int]] = (64, 56, 48)
PHANTOM_SPACING_MM: Final[tuple[float, float, float]] = (1.0, 1.25, 2.0)
PHANTOM_ORIGIN_MM: Final[tuple[float, float, float]] = (-28.0, -30.0, -40.0)

# Low enough to sit under every marker, high enough to render as a body in a viewer. The
# background exists only so the volume looks like something during the by-hand check in three
# independent tools that docs/06 asks for. Nothing asserts against it.
BACKGROUND_INTENSITY: Final[int] = 30


@dataclass(frozen=True)
class PhantomMarker:
    """One marker box, its anatomical claim, and its hand-computed answer.

    ``expected_centre_mm`` and ``expected_voxel_count`` are not recorded output. They were
    worked out on paper from the box bounds and the affine, and the arithmetic is in
    ``PHANTOM_MARKERS`` below. A test asserts the generator reproduces them, so an edit to a
    box that changes the geometry cannot pass quietly.

    If that test ever fails, re-derive the constant by hand. Do not copy the value the code
    printed: that turns the only independent check in this file into a tautology.
    """

    label: str
    intensity: int
    axis: Axis
    expected_pole: Pole
    i_range: tuple[int, int]
    j_range: tuple[int, int]
    k_range: tuple[int, int]
    expected_centre_mm: WorldPoint
    expected_voxel_count: int


# Voxel index i maps to RAS x as `i * 1.00 - 28.0`, j to y as `j * 1.25 - 30.0`, and k to z as
# `k * 2.00 - 40.0`. Ranges below are half-open. Each centre is the mean of the integer voxel
# indices in the box, put through those three expressions.
PHANTOM_MARKERS: Final[tuple[PhantomMarker, ...]] = (
    # i 6..18 mean 12  -> x = 12*1.00 - 28.0 = -16.0   (left, and nowhere near midline)
    # j 20..32 mean 26 -> y = 26*1.25 - 30.0 =  +2.5
    # k 18..30 mean 24 -> z = 24*2.00 - 40.0 =  +8.0
    PhantomMarker(
        label="left-block",
        intensity=200,
        axis=Axis.LEFT_RIGHT,
        expected_pole=Pole.LEFT,
        i_range=(6, 19),
        j_range=(20, 33),
        k_range=(18, 31),
        expected_centre_mm=WorldPoint(-16.0, 2.5, 8.0),
        expected_voxel_count=13 * 13 * 13,
    ),
    # i 24..32 mean 28 -> x = 28*1.00 - 28.0 =   0.0   (exactly midline, by construction)
    # j 42..50 mean 46 -> y = 46*1.25 - 30.0 = +27.5   (anterior)
    # k 12..20 mean 16 -> z = 16*2.00 - 40.0 =  -8.0
    PhantomMarker(
        label="anterior-wedge",
        intensity=150,
        axis=Axis.POSTERIOR_ANTERIOR,
        expected_pole=Pole.ANTERIOR,
        i_range=(24, 33),
        j_range=(42, 51),
        k_range=(12, 21),
        expected_centre_mm=WorldPoint(0.0, 27.5, -8.0),
        expected_voxel_count=9 * 9 * 9,
    ),
    # i 24..32 mean 28 -> x = 28*1.00 - 28.0 =   0.0   (exactly midline, by construction)
    # j 21..31 mean 26 -> y = 26*1.25 - 30.0 =  +2.5
    # k 36..46 mean 41 -> z = 41*2.00 - 40.0 = +42.0   (superior)
    PhantomMarker(
        label="superior-cap",
        intensity=100,
        axis=Axis.INFERIOR_SUPERIOR,
        expected_pole=Pole.SUPERIOR,
        i_range=(24, 33),
        j_range=(21, 32),
        k_range=(36, 47),
        expected_centre_mm=WorldPoint(0.0, 2.5, 42.0),
        expected_voxel_count=9 * 11 * 11,
    ),
)


@dataclass(frozen=True)
class Phantom:
    """A volume, its affine, and the markers whose anatomy it claims.

    ``data`` is set read-only. The phantom is the reference every geometry stage is measured
    against, and a stage that mutated it in place would leave every later assertion in the
    run checking against evidence the stage itself had edited.
    """

    data: np.ndarray
    affine: np.ndarray
    markers: tuple[PhantomMarker, ...]

    @property
    def axis_codes(self) -> tuple[str, str, str]:
        return axis_codes(self.affine)

    def to_nifti(self):  # type: ignore[no-untyped-def]
        """Wrap as a ``nibabel.Nifti1Image``, for writing out or loading into a viewer.

        Imported inside the function so the rest of this module stays importable without
        touching nibabel's image machinery, which the pure-geometry tests do not need.
        """
        import nibabel as nib

        return nib.Nifti1Image(self.data, self.affine)


def build_phantom() -> Phantom:
    """Build the phantom. Deterministic, no inputs, bit-identical on every machine."""
    affine = _phantom_affine()
    data = _background_ellipsoid()
    for marker in PHANTOM_MARKERS:
        _draw_box(data, marker)
    data.flags.writeable = False
    affine.flags.writeable = False
    return Phantom(data=data, affine=affine, markers=PHANTOM_MARKERS)


def reorient(
    data: np.ndarray,
    affine: np.ndarray,
    target_codes: tuple[str, str, str],
) -> tuple[np.ndarray, np.ndarray]:
    """Rewrite a volume in a different voxel order, preserving the physical object.

    This is what pipeline stage 3 does, and the property that makes it correct is that it
    changes both the array and the affine together, so every world coordinate is unchanged.
    Run the orientation report before and after: the voxel indices move, the millimetres do
    not, and the report is identical.

    Delegates the index bookkeeping to ``nibabel.orientations`` rather than reimplementing it.
    Hand-rolled axis permutation logic is a well known way to introduce the exact bug this
    module exists to catch.
    """
    start = io_orientation(np.asarray(affine, dtype=np.float64))
    transform = ornt_transform(start, axcodes2ornt(target_codes))
    moved = apply_orientation(np.asarray(data), transform)
    corrected = np.asarray(affine, dtype=np.float64) @ inv_ornt_aff(transform, data.shape)
    return moved, corrected


def break_orientation(
    data: np.ndarray,
    affine: np.ndarray,
    voxel_axis: int,
) -> tuple[np.ndarray, np.ndarray]:
    """Flip the data along ``voxel_axis`` and leave the affine alone. Deliberately wrong.

    This is the fixture ``docs/06`` asks for when it says to break the orientation on purpose
    and observe how invisible the failure is, and the broken fixture per failure class that
    ``docs/16`` requires. It exists so a test can assert the orientation report **fails**.

    An assertion nobody has watched fail is not known to work, and this one guards a failure
    mode that produces no symptom of its own. Never call this outside a test.
    """
    if voxel_axis not in (0, 1, 2):
        raise ValueError(f"voxel_axis must be 0, 1 or 2, got {voxel_axis}")
    return np.flip(np.asarray(data), axis=voxel_axis).copy(), np.asarray(affine).copy()


def orientation_report(
    data: np.ndarray,
    affine: np.ndarray,
    markers: tuple[PhantomMarker, ...] = PHANTOM_MARKERS,
    tolerance_mm: float = 1.0,
) -> OrientationReport:
    """Check every marker and assemble the QC orientation panel.

    Reports on all markers rather than stopping at the first failure. Rule 4, rank never
    suppress, applies to diagnostics too: knowing that two of three markers moved says
    "transpose", knowing only that the first one moved says almost nothing.
    """
    checks: list[MarkerCheck] = [
        check_marker(
            data,
            affine,
            label=marker.label,
            intensity=marker.intensity,
            axis=marker.axis,
            expected=marker.expected_pole,
            tolerance_mm=tolerance_mm,
        )
        for marker in markers
    ]
    return OrientationReport(
        axis_codes=axis_codes(affine),
        determinant_sign=determinant_sign(affine),
        voxel_sizes_mm=voxel_sizes_mm(affine),
        checks=tuple(checks),
    )


def _phantom_affine() -> np.ndarray:
    """Voxel indices to RAS+ millimetres: i toward the right, j anterior, k superior."""
    affine = np.eye(4, dtype=np.float64)
    affine[0, 0], affine[1, 1], affine[2, 2] = PHANTOM_SPACING_MM
    affine[:3, 3] = PHANTOM_ORIGIN_MM
    return affine


def _background_ellipsoid() -> np.ndarray:
    """A soft body so the volume renders as an object during the by-hand viewer check.

    Cosmetic only. Every assertion in this package addresses a marker by its intensity, so
    nothing depends on the shape, the extent, or whether a marker pokes out of it.
    """
    ni, nj, nk = PHANTOM_SHAPE
    i, j, k = np.ogrid[0:ni, 0:nj, 0:nk]
    centre = ((ni - 1) / 2.0, (nj - 1) / 2.0, (nk - 1) / 2.0)
    semi_axes = (ni / 2.1, nj / 2.1, nk / 2.1)
    radial = (
        ((i - centre[0]) / semi_axes[0]) ** 2
        + ((j - centre[1]) / semi_axes[1]) ** 2
        + ((k - centre[2]) / semi_axes[2]) ** 2
    )
    data = np.zeros(PHANTOM_SHAPE, dtype=np.uint8)
    data[radial <= 1.0] = BACKGROUND_INTENSITY
    return data


def _draw_box(data: np.ndarray, marker: PhantomMarker) -> None:
    """Write a marker into ``data``, refusing to clip it silently.

    A box that runs off the edge of the array would be written truncated by ordinary numpy
    slicing, and its centre of mass would then be wrong by an amount nobody would notice.
    """
    for name, (low, high), extent in zip(
        ("i", "j", "k"),
        (marker.i_range, marker.j_range, marker.k_range),
        PHANTOM_SHAPE,
    ):
        if not 0 <= low < high <= extent:
            raise ValueError(
                f"marker {marker.label!r} has {name} range [{low}, {high}) outside the "
                f"phantom's {name} extent of {extent}. numpy would have clipped it and moved "
                f"its centre of mass without complaint."
            )
    i_low, i_high = marker.i_range
    j_low, j_high = marker.j_range
    k_low, k_high = marker.k_range
    data[i_low:i_high, j_low:j_high, k_low:k_high] = marker.intensity
