"""Bland-Altman agreement for volume error, because a mean error is not an agreement claim.

``docs/10-EVALUATION_PROTOCOL.md``, on volume error: "Report as Bland-Altman with limits of
agreement, not as a mean. A mean error near zero can hide large scatter."

That sentence is the whole reason this module exists rather than a call to ``np.mean``. A
segmenter that over-calls by 20 ml on half the cohort and under-calls by 20 ml on the other
half has a mean error of zero and is useless. The limits of agreement are what say so: they
are the interval within which 95% of individual differences fall, and for that segmenter they
would be roughly ±40 ml, which no reader would mistake for agreement.

What is computed, stated so the thesis can state it
---------------------------------------------------
For each case, the **difference** is prediction minus reference, in millilitres, so a positive
difference is over-segmentation. The **mean** is ``(prediction + reference) / 2``, the standard
Bland-Altman abscissa, used because the reference is itself a measurement rather than a truth
and plotting against it induces a spurious correlation.

- **Bias** is the mean of the differences.
- **SD** is the sample standard deviation of the differences, ``ddof=1``. The population form
  understates the interval on the cohort sizes this project will have.
- **Limits of agreement** are ``bias ± 1.96 * SD``. The 1.96 is the normal approximation, and
  it is an approximation: it assumes the differences are roughly normal and that their scatter
  does not grow with lesion size. Neither is guaranteed here, which is why
  ``proportional_bias_r`` is computed and reported beside them rather than left for a reader
  to wonder about.

``proportional_bias_r`` is the Pearson correlation between the differences and the means. It is
the standard check on the second assumption: a large magnitude means the error grows with
lesion size, the single limits of agreement are then misleading across the size range, and
table 4.1's size bands are where that has to be read instead.
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Final

import numpy as np

from .metrics import Degeneracy, VolumeError

__all__ = [
    "LOA_Z",
    "BlandAltman",
    "MIN_CASES",
    "bland_altman",
    "bland_altman_of",
]

# The normal approximation for a 95% interval. Named rather than inlined because it is an
# assumption the thesis has to defend, not a magic constant.
LOA_Z: Final[float] = 1.96

# Two differences give a sample standard deviation, and it is a meaningless one. Below this
# the limits of agreement are not a weak result, they are not a result.
MIN_CASES: Final[int] = 3


@dataclass(frozen=True)
class BlandAltman:
    """A volume-agreement result, in the shape table 4.1's last column needs.

    ``n_excluded`` is carried alongside ``n`` for the same reason ``Summary`` carries
    ``n_undefined``: cases whose volume error is undefined were dropped to compute this, and a
    number that does not say how many were dropped is not readable.
    """

    unit: str
    n: int
    n_excluded: int
    bias: float
    sd_difference: float
    loa_low: float
    loa_high: float
    proportional_bias_r: float | None

    @property
    def n_total(self) -> int:
        return self.n + self.n_excluded

    def as_table_cell(self) -> str:
        """The ``bias [95% LoA]`` form of table 4.1's volume-error column."""
        cell = f"{self.bias:+.2f} [{self.loa_low:+.2f}, {self.loa_high:+.2f}] (n={self.n}"
        if self.n_excluded:
            cell += f" of {self.n_total}, {self.n_excluded} undefined"
        return cell + ")"

    def describe(self) -> str:
        lines = [
            f"Bland-Altman, {self.unit}: bias {self.bias:+.3f}, SD {self.sd_difference:.3f}, "
            f"95% limits of agreement [{self.loa_low:+.3f}, {self.loa_high:+.3f}], "
            f"n={self.n} of {self.n_total}"
        ]
        if self.proportional_bias_r is None:
            lines.append("  proportional bias: not computable, the case means have no spread")
        else:
            lines.append(
                f"  proportional bias r={self.proportional_bias_r:+.3f} between the "
                f"differences and the case means"
            )
        return "\n".join(lines)


class BlandAltmanError(ValueError):
    """The cohort cannot support limits of agreement."""


def bland_altman(
    differences: Sequence[float],
    means: Sequence[float],
    *,
    unit: str,
    n_excluded: int = 0,
) -> BlandAltman:
    """Bias, limits of agreement and proportional bias from paired differences and means.

    Takes the two derived sequences rather than the raw measurements so it can be used for any
    paired quantity — lesion volume today, involved region count for table 4.3 later — and so
    the known-answer test can pass in numbers whose answer was worked out on paper.

    Raises rather than returning a degraded result when there are fewer than ``MIN_CASES``
    cases. Every other module here returns a value with a degeneracy flag instead of raising,
    and the difference is deliberate: an undefined Dice on one case is an ordinary event in a
    cohort, whereas limits of agreement over two cases is not a weaker claim, it is not the
    claim at all, and there is no honest table cell for it.
    """
    if len(differences) != len(means):
        raise BlandAltmanError(
            f"got {len(differences)} differences and {len(means)} means; they are per-case "
            f"and must be paired"
        )
    if len(differences) < MIN_CASES:
        raise BlandAltmanError(
            f"limits of agreement need at least {MIN_CASES} cases, got {len(differences)}. "
            f"Report the individual differences instead; a limit of agreement over "
            f"{len(differences)} cases would read as a cohort result and is not one."
        )

    d = np.asarray(differences, dtype=np.float64)
    m = np.asarray(means, dtype=np.float64)
    if not np.all(np.isfinite(d)) or not np.all(np.isfinite(m)):
        raise BlandAltmanError(
            "differences and means must all be finite. A non-finite value here is an "
            "undefined case that was not excluded upstream."
        )

    bias = float(d.mean())
    sd = float(d.std(ddof=1))
    return BlandAltman(
        unit=unit,
        n=int(d.size),
        n_excluded=int(n_excluded),
        bias=bias,
        sd_difference=sd,
        loa_low=bias - LOA_Z * sd,
        loa_high=bias + LOA_Z * sd,
        proportional_bias_r=_pearson(d, m),
    )


def bland_altman_of(
    errors: Sequence[VolumeError],
    *,
    unit: str = "ml",
) -> BlandAltman:
    """Limits of agreement over a cohort of ``VolumeError`` results.

    Cases flagged ``BOTH_EMPTY`` are excluded and counted. A case where neither the prediction
    nor the reference contains any lesion has a volume difference of exactly zero, and it is a
    true zero — but it is a zero from a case with nothing to segment, and letting it into the
    cohort pulls the bias toward zero and tightens the limits of agreement for a reason that
    has nothing to do with how well the segmenter works.

    Every other degeneracy stays in. An empty prediction against a real reference is a real,
    and large, volume error; excluding it would be the single most flattering thing this
    module could do.
    """
    kept = [error for error in errors if error.degeneracy is not Degeneracy.BOTH_EMPTY]
    differences = [error.signed_ml for error in kept]
    means = [(error.prediction_ml + error.reference_ml) / 2.0 for error in kept]
    return bland_altman(
        differences,
        means,
        unit=unit,
        n_excluded=len(errors) - len(kept),
    )


def _pearson(differences: np.ndarray, means: np.ndarray) -> float | None:
    """Correlation between the differences and the case means, or ``None`` if undefined.

    ``None`` rather than zero when either sequence is constant. A correlation of zero says
    "checked, no proportional bias"; there is no such finding when the means are all equal,
    and reporting one would be an answer to a question that was never askable.
    """
    d_sd = float(differences.std(ddof=1))
    m_sd = float(means.std(ddof=1))
    if d_sd == 0.0 or m_sd == 0.0:
        return None
    r = float(np.corrcoef(differences, means)[0, 1])
    return None if math.isnan(r) else r
