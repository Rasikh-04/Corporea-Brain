"""Bland-Altman, against numbers worked out on paper.

``docs/10`` asks for limits of agreement precisely because a mean can hide scatter, so the
test that matters most here is the one where the mean is zero and the limits are wide. It is
``test_a_zero_mean_error_does_not_mean_agreement`` below, and it is the failure mode the
metric exists to expose.
"""

from __future__ import annotations

import numpy as np
import pytest
from corporea_eval.bland_altman import (
    LOA_Z,
    MIN_CASES,
    BlandAltmanError,
    bland_altman,
    bland_altman_of,
)
from corporea_eval.metrics import Degeneracy, VolumeError


def _error(prediction_ml: float, reference_ml: float, degeneracy: Degeneracy) -> VolumeError:
    signed = prediction_ml - reference_ml
    return VolumeError(
        prediction_ml=prediction_ml,
        reference_ml=reference_ml,
        signed_ml=signed,
        absolute_ml=abs(signed),
        relative=None if reference_ml == 0.0 else signed / reference_ml,
        degeneracy=degeneracy,
    )


@pytest.mark.known_answer
def test_bias_and_limits_are_hand_computable() -> None:
    """Differences 1, 2, 3, 4, 5 ml.

    Mean is ``15 / 5 = 3.0``. The deviations are -2, -1, 0, 1, 2, so the sum of squares is
    ``4 + 1 + 0 + 1 + 4 = 10`` and the sample variance is ``10 / (5 - 1) = 2.5``, giving
    ``SD = sqrt(2.5) = 1.5811388...``. The limits are ``3.0 ± 1.96 * 1.5811388``, that is
    ``[-0.09903..., +6.09903...]``.
    """
    differences = [1.0, 2.0, 3.0, 4.0, 5.0]
    means = [10.0, 20.0, 30.0, 40.0, 50.0]

    result = bland_altman(differences, means, unit="ml")

    assert result.n == 5
    assert result.bias == pytest.approx(3.0)
    assert result.sd_difference == pytest.approx(2.5**0.5)
    assert result.loa_low == pytest.approx(3.0 - LOA_Z * 2.5**0.5)
    assert result.loa_high == pytest.approx(3.0 + LOA_Z * 2.5**0.5)


@pytest.mark.known_answer
def test_a_zero_mean_error_does_not_mean_agreement() -> None:
    """The sentence in ``docs/10`` made into a test.

    A segmenter that over-calls by 20 ml on half the cohort and under-calls by 20 ml on the
    other half has a mean error of exactly zero and is useless. The differences are
    ±20 with a sample SD of ``sqrt(1600 / 3)`` over four cases, which is ``23.094...``, so the
    limits are ``±45.26...`` ml. Nobody reads that as agreement, which is the point.
    """
    differences = [20.0, -20.0, 20.0, -20.0]
    means = [50.0, 60.0, 70.0, 80.0]

    result = bland_altman(differences, means, unit="ml")

    assert result.bias == pytest.approx(0.0)
    assert result.sd_difference == pytest.approx((1600.0 / 3.0) ** 0.5)
    assert result.loa_high == pytest.approx(LOA_Z * (1600.0 / 3.0) ** 0.5)
    assert result.loa_high - result.loa_low > 90.0


def test_the_table_cell_shows_bias_and_both_limits() -> None:
    result = bland_altman([1.0, 2.0, 3.0], [10.0, 20.0, 30.0], unit="ml")

    cell = result.as_table_cell()

    assert cell.startswith("+2.00 [")
    assert "n=3" in cell


def test_the_table_cell_says_how_many_cases_were_dropped() -> None:
    """A cell reporting n=3 out of an unstated cohort is the cell an examiner asks about."""
    result = bland_altman([1.0, 2.0, 3.0], [10.0, 20.0, 30.0], unit="ml", n_excluded=2)

    cell = result.as_table_cell()

    assert "n=3 of 5, 2 undefined" in cell


# --- Proportional bias --------------------------------------------------------------------


def test_proportional_bias_is_reported_when_the_error_grows_with_lesion_size() -> None:
    """Differences rising with the means is exactly the case the single LoA misrepresents."""
    result = bland_altman([1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0], unit="ml")

    assert result.proportional_bias_r == pytest.approx(1.0)


def test_proportional_bias_is_none_rather_than_zero_when_it_cannot_be_computed() -> None:
    """Constant means give no correlation to report, and zero would read as "checked, none"."""
    result = bland_altman([1.0, 2.0, 3.0], [10.0, 10.0, 10.0], unit="ml")

    assert result.proportional_bias_r is None


# --- Refusals -----------------------------------------------------------------------------


def test_a_cohort_too_small_for_limits_of_agreement_is_refused() -> None:
    """Not a degraded result. There is no honest table cell for LoA over two cases."""
    with pytest.raises(BlandAltmanError, match=f"at least {MIN_CASES} cases"):
        bland_altman([1.0, 2.0], [10.0, 20.0], unit="ml")


def test_unpaired_inputs_are_refused() -> None:
    with pytest.raises(BlandAltmanError, match="paired"):
        bland_altman([1.0, 2.0, 3.0], [10.0, 20.0], unit="ml")


def test_a_non_finite_difference_is_refused_as_an_unexcluded_case() -> None:
    with pytest.raises(BlandAltmanError, match="finite"):
        bland_altman([1.0, 2.0, float("nan")], [10.0, 20.0, 30.0], unit="ml")


# --- Over a cohort of VolumeError ---------------------------------------------------------


def test_both_empty_cases_are_excluded_and_counted() -> None:
    """A case with no lesion to segment contributes a true zero that flatters the result."""
    errors = [
        _error(12.0, 10.0, Degeneracy.NONE),
        _error(8.0, 10.0, Degeneracy.NONE),
        _error(14.0, 10.0, Degeneracy.NONE),
        _error(0.0, 0.0, Degeneracy.BOTH_EMPTY),
        _error(0.0, 0.0, Degeneracy.BOTH_EMPTY),
    ]

    result = bland_altman_of(errors)

    assert result.n == 3
    assert result.n_excluded == 2
    assert result.n_total == 5
    assert result.bias == pytest.approx((2.0 - 2.0 + 4.0) / 3.0)


def test_a_total_miss_stays_in_the_cohort() -> None:
    """Excluding the cases that failed completely is the most flattering thing available."""
    errors = [
        _error(12.0, 10.0, Degeneracy.NONE),
        _error(8.0, 10.0, Degeneracy.NONE),
        _error(0.0, 30.0, Degeneracy.PREDICTION_EMPTY),
    ]

    result = bland_altman_of(errors)

    assert result.n == 3
    assert result.n_excluded == 0
    assert result.bias == pytest.approx((2.0 - 2.0 - 30.0) / 3.0)


def test_the_mean_axis_is_the_case_mean_not_the_reference() -> None:
    """Plotting against the reference induces a correlation that is not in the data.

    Constructed so the two choices disagree: the differences here correlate perfectly with the
    references and not at all with the case means, so a module that used the reference as the
    abscissa would report ``r = 1`` where the correct answer is ``0``.
    """
    errors = [
        _error(9.0, 11.0, Degeneracy.NONE),
        _error(10.0, 10.0, Degeneracy.NONE),
        _error(11.0, 9.0, Degeneracy.NONE),
    ]

    result = bland_altman_of(errors)

    assert [error.reference_ml for error in errors] == [11.0, 10.0, 9.0]
    assert result.proportional_bias_r is None or abs(result.proportional_bias_r) < 1e-9
    assert np.corrcoef(
        [error.signed_ml for error in errors],
        [error.reference_ml for error in errors],
    )[0, 1] == pytest.approx(-1.0)
