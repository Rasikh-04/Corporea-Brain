"""Segmentation metrics: Dice, HD95, ASSD, volume error.

``docs/10-EVALUATION_PROTOCOL.md`` calls the known-answer test on hand-computed Dice the
single highest-value test in the repository, and says to write it first. It was.

Why a metric needs more care than the thing it measures
-------------------------------------------------------
A broken segmenter produces obviously bad masks. A broken metric produces **plausible
numbers**, which are then transcribed into a results table, defended at a viva, and believed.
There is no downstream check that catches it.

So two rules hold throughout this module.

**Distances are in millimetres, never in voxels.** Every surface metric takes the voxel
spacing and uses it. Clinical acquisitions are routinely anisotropic, often severely so
through-plane, and a metric that quietly measures in voxel units is wrong by the spacing
ratio without any sign of it.

**No result is a bare float.** Every metric returns a value together with a degeneracy flag,
because the degenerate cases are exactly where a metric lies. An empty prediction has no
surface, so HD95 is undefined; returning ``0.0`` would read as a perfect boundary match on the
one case that failed completely. ``docs/16`` puts it as: a defined result or a defined error,
never a silent ``NaN``.

Conventions this module fixes, because they vary in the literature
------------------------------------------------------------------
Stated here so the thesis can state them, and so nobody has to read the source to find out.

- **Surface voxels** are mask voxels with at least one background neighbour under
  6-connectivity. A mask touching the edge of the array counts that face as surface: the data
  gives no way to tell a clipped field of view from a real boundary, and treating it as
  surface is the conservative reading.
- **HD95** is ``max(p95(d(pred -> ref)), p95(d(ref -> pred)))``, the symmetric form used by
  BraTS, not the 95th percentile of the pooled distances. The percentile itself is numpy's
  default linear interpolation.
- **ASSD** is the pooled mean, ``(sum(d_pr) + sum(d_rp)) / (n_pr + n_rp)``, not the mean of
  the two directed means. The two differ whenever the surfaces have different sizes, which is
  always.
- **Dice on two empty masks is 1.0**, flagged ``BOTH_EMPTY``. They agree perfectly, and the
  flag is what stops that agreement being averaged into a table of lesion scores. See
  ``aggregate.py``.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Final

import numpy as np
from scipy.ndimage import binary_erosion, distance_transform_edt, generate_binary_structure

__all__ = [
    "Degeneracy",
    "MetricResult",
    "VolumeError",
    "MetricError",
    "dice",
    "hd95",
    "assd",
    "volume_error",
    "surface_distances_mm",
]

HD_PERCENTILE: Final[float] = 95.0
MM3_PER_ML: Final[float] = 1000.0


class MetricError(ValueError):
    """The inputs cannot support a metric at all: wrong shape, bad spacing, not a mask.

    Distinct from a degeneracy. A degeneracy is a real case with an awkward answer, such as a
    model that predicted nothing. This is a caller mistake, and it stops the run.
    """


class Degeneracy(Enum):
    """Why a metric's value needs reading with care, or is missing entirely.

    Travels with the value everywhere so that no aggregation can lose it.
    """

    NONE = "none"
    BOTH_EMPTY = "both-empty"
    PREDICTION_EMPTY = "prediction-empty"
    REFERENCE_EMPTY = "reference-empty"


@dataclass(frozen=True)
class MetricResult:
    """One metric on one case. ``value`` is ``None`` when the metric is genuinely undefined.

    ``None`` rather than ``NaN`` on purpose. ``NaN`` propagates silently through a mean and
    through a comparison, and turns up in a table as a blank cell nobody can account for.
    ``None`` fails loudly at the point where somebody tries to use it as a number.
    """

    name: str
    value: float | None
    unit: str
    degeneracy: Degeneracy
    detail: str = ""

    @property
    def is_defined(self) -> bool:
        return self.value is not None

    def __str__(self) -> str:
        shown = "undefined" if self.value is None else f"{self.value:.6g} {self.unit}"
        flag = "" if self.degeneracy is Degeneracy.NONE else f" [{self.degeneracy.value}]"
        return f"{self.name} = {shown}{flag}"


@dataclass(frozen=True)
class VolumeError:
    """Predicted against reference volume, in millilitres.

    ``signed_ml`` is prediction minus reference, so a positive value is over-segmentation.
    The sign is kept because ``docs/10`` requires Bland-Altman with limits of agreement, and
    an unsigned error cannot produce one: a mean near zero would hide a model that alternates
    between large over- and under-calls.

    ``relative`` is ``None`` when the reference is empty. Dividing by zero reference volume is
    undefined, and substituting a large number would rank that case as the worst failure
    rather than as one that cannot be scored this way.
    """

    prediction_ml: float
    reference_ml: float
    signed_ml: float
    absolute_ml: float
    relative: float | None
    degeneracy: Degeneracy


def dice(prediction: np.ndarray, reference: np.ndarray) -> MetricResult:
    """Dice similarity coefficient, ``2|A and B| / (|A| + |B|)``.

    Severely misleading for small lesions: a 2 ml acute stroke can be localised perfectly and
    still score badly, because a one-voxel boundary shift costs a large fraction of a small
    mask. ``docs/10`` therefore makes stratification by lesion volume band mandatory for E1,
    and this function is not the place that can enforce it. Report Dice stratified, and always
    beside HD95 and ASSD.
    """
    predicted, referenced = _as_masks(prediction, reference)
    n_prediction = int(predicted.sum())
    n_reference = int(referenced.sum())
    degeneracy = _degeneracy_of(n_prediction, n_reference)

    if degeneracy is Degeneracy.BOTH_EMPTY:
        return MetricResult(
            name="dice",
            value=1.0,
            unit="",
            degeneracy=degeneracy,
            detail=(
                "both masks empty: 2*0/(0+0) is undefined and reported as perfect agreement, "
                "which is defensible for a case with no lesion and indefensible averaged into "
                "a table of lesion scores. Partition on this flag before aggregating."
            ),
        )
    if degeneracy is not Degeneracy.NONE:
        return MetricResult(
            name="dice",
            value=0.0,
            unit="",
            degeneracy=degeneracy,
            detail="one mask empty and the other not: no overlap is possible.",
        )

    overlap = int(np.logical_and(predicted, referenced).sum())
    return MetricResult(
        name="dice",
        value=2.0 * overlap / (n_prediction + n_reference),
        unit="",
        degeneracy=Degeneracy.NONE,
    )


def hd95(
    prediction: np.ndarray,
    reference: np.ndarray,
    spacing_mm: tuple[float, float, float],
) -> MetricResult:
    """95th percentile symmetric Hausdorff distance, in millimetres.

    Sensitive to a single distant false-positive component, which is a property rather than a
    defect: one spurious blob in the contralateral hemisphere is exactly the failure a
    clinician needs told about. ``docs/10`` asks for a connected-component count alongside, so
    that a large HD95 can be attributed to a stray component rather than to a diffuse boundary
    error.
    """
    return _surface_metric("hd95", prediction, reference, spacing_mm, _hd95_from)


def assd(
    prediction: np.ndarray,
    reference: np.ndarray,
    spacing_mm: tuple[float, float, float],
) -> MetricResult:
    """Average symmetric surface distance, in millimetres.

    More stable than HD95 and less intuitive, so ``docs/10`` requires both.
    """
    return _surface_metric("assd", prediction, reference, spacing_mm, _assd_from)


def volume_error(
    prediction: np.ndarray,
    reference: np.ndarray,
    spacing_mm: tuple[float, float, float],
) -> VolumeError:
    """Predicted against reference lesion volume in millilitres, signed and absolute."""
    predicted, referenced = _as_masks(prediction, reference)
    _validate_spacing(spacing_mm)
    ml_per_voxel = float(np.prod(spacing_mm)) / MM3_PER_ML

    prediction_ml = int(predicted.sum()) * ml_per_voxel
    reference_ml = int(referenced.sum()) * ml_per_voxel
    signed = prediction_ml - reference_ml

    return VolumeError(
        prediction_ml=prediction_ml,
        reference_ml=reference_ml,
        signed_ml=signed,
        absolute_ml=abs(signed),
        relative=None if reference_ml == 0.0 else signed / reference_ml,
        degeneracy=_degeneracy_of(int(predicted.sum()), int(referenced.sum())),
    )


def surface_distances_mm(
    source: np.ndarray,
    target: np.ndarray,
    spacing_mm: tuple[float, float, float],
) -> np.ndarray:
    """Distance in millimetres from every surface voxel of ``source`` to ``target``'s surface.

    Exposed because the directed distributions are worth plotting when a case scores badly.
    A histogram distinguishes a uniformly loose boundary from a tight one with a single stray
    component, and those call for different fixes.
    """
    source_mask, target_mask = _as_masks(source, target)
    _validate_spacing(spacing_mm)
    source_surface = _surface_of(source_mask)
    target_surface = _surface_of(target_mask)
    if not source_surface.any() or not target_surface.any():
        raise MetricError(
            "surface distance needs a surface on both sides. An empty mask has none, and the "
            "distance is undefined rather than large or zero."
        )
    return _distances_to(source_surface, target_surface, spacing_mm)


def _surface_metric(name, prediction, reference, spacing_mm, reduce):  # type: ignore[no-untyped-def]
    """Shared shape for HD95 and ASSD: same degeneracies, same distances, different reduction."""
    predicted, referenced = _as_masks(prediction, reference)
    _validate_spacing(spacing_mm)
    degeneracy = _degeneracy_of(int(predicted.sum()), int(referenced.sum()))

    if degeneracy is not Degeneracy.NONE:
        return MetricResult(
            name=name,
            value=None,
            unit="mm",
            degeneracy=degeneracy,
            detail=(
                "at least one mask is empty and so has no surface. The distance is undefined. "
                "Reporting 0.0 here would read as a perfect boundary match on a case that "
                "failed completely."
            ),
        )

    forward = _distances_to(_surface_of(predicted), _surface_of(referenced), spacing_mm)
    backward = _distances_to(_surface_of(referenced), _surface_of(predicted), spacing_mm)
    return MetricResult(
        name=name,
        value=float(reduce(forward, backward)),
        unit="mm",
        degeneracy=Degeneracy.NONE,
    )


def _hd95_from(forward: np.ndarray, backward: np.ndarray) -> float:
    return max(
        float(np.percentile(forward, HD_PERCENTILE)),
        float(np.percentile(backward, HD_PERCENTILE)),
    )


def _assd_from(forward: np.ndarray, backward: np.ndarray) -> float:
    return float(
        (forward.sum() + backward.sum()) / (forward.size + backward.size)
    )


def _surface_of(mask: np.ndarray) -> np.ndarray:
    """Mask voxels with at least one background neighbour under 6-connectivity.

    ``border_value=0`` treats everything outside the array as background, so a mask running
    into the edge of the volume counts that face as surface.
    """
    structure = generate_binary_structure(mask.ndim, 1)
    interior = binary_erosion(mask, structure=structure, border_value=0)
    return np.logical_and(mask, np.logical_not(interior))


def _distances_to(
    source_surface: np.ndarray,
    target_surface: np.ndarray,
    spacing_mm: tuple[float, float, float],
) -> np.ndarray:
    """Millimetre distance from each ``source_surface`` voxel to the nearest target surface.

    ``sampling=spacing_mm`` is the whole reason this is not a voxel count. Drop it and every
    surface metric silently becomes wrong by the anisotropy ratio.
    """
    to_target = distance_transform_edt(
        np.logical_not(target_surface), sampling=spacing_mm
    )
    return np.asarray(to_target)[source_surface]


def _degeneracy_of(n_prediction: int, n_reference: int) -> Degeneracy:
    if n_prediction == 0 and n_reference == 0:
        return Degeneracy.BOTH_EMPTY
    if n_prediction == 0:
        return Degeneracy.PREDICTION_EMPTY
    if n_reference == 0:
        return Degeneracy.REFERENCE_EMPTY
    return Degeneracy.NONE


def _as_masks(
    prediction: np.ndarray, reference: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    predicted = np.asarray(prediction)
    referenced = np.asarray(reference)
    if predicted.shape != referenced.shape:
        raise MetricError(
            f"prediction shape {predicted.shape} does not match reference shape "
            f"{referenced.shape}. These are not the same case, or one was not resampled."
        )
    if predicted.ndim != 3:
        raise MetricError(f"expected a 3D volume, got {predicted.ndim} dimensions")
    return predicted.astype(bool), referenced.astype(bool)


def _validate_spacing(spacing_mm: tuple[float, float, float]) -> None:
    if len(spacing_mm) != 3:
        raise MetricError(f"spacing must have three components, got {len(spacing_mm)}")
    if not all(np.isfinite(spacing_mm)) or any(s <= 0.0 for s in spacing_mm):
        raise MetricError(
            f"spacing must be finite and positive, got {spacing_mm}. A zero or missing "
            f"spacing is how a millimetre metric silently becomes a voxel count."
        )
