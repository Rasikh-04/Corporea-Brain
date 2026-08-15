"""Degenerate inputs: empty, single voxel, disjoint, mismatched.

``docs/16-TESTING_STRATEGY.md``: each must produce a defined result or a defined error, never
a silent ``NaN``.

These are the cases where a metric lies. An empty prediction is not rare in a real cohort: it
is what a model does on the hardest case in the set, which is exactly the case whose score
must not be quietly favourable.
"""

from __future__ import annotations

import numpy as np
import pytest

from braintwin_eval.aggregate import UndefinedPolicy, summarise
from braintwin_eval.metrics import (
    Degeneracy,
    MetricError,
    assd,
    dice,
    hd95,
    surface_distances_mm,
    volume_error,
)

ISOTROPIC = (1.0, 1.0, 1.0)
SHAPE = (6, 4, 4)


@pytest.fixture
def empty() -> np.ndarray:
    return np.zeros(SHAPE, dtype=bool)


@pytest.fixture
def single_voxel() -> np.ndarray:
    mask = np.zeros(SHAPE, dtype=bool)
    mask[1, 1, 1] = True
    return mask


class TestBothEmpty:
    def test_dice_reports_agreement_but_flags_it(self, empty) -> None:
        result = dice(empty, empty)
        assert result.value == pytest.approx(1.0)
        assert result.degeneracy is Degeneracy.BOTH_EMPTY
        assert "indefensible" in result.detail

    @pytest.mark.parametrize("metric", [hd95, assd])
    def test_surface_metrics_are_undefined_not_zero(self, metric, empty) -> None:
        # Zero would read as a perfect boundary match. There is no boundary.
        result = metric(empty, empty, ISOTROPIC)
        assert result.value is None
        assert not result.is_defined
        assert result.degeneracy is Degeneracy.BOTH_EMPTY

    def test_volume_error_is_zero_and_relative_is_undefined(self, empty) -> None:
        result = volume_error(empty, empty, ISOTROPIC)
        assert result.signed_ml == pytest.approx(0.0)
        assert result.relative is None


class TestOneEmpty:
    def test_dice_is_zero_when_the_prediction_is_empty(self, empty, single_voxel) -> None:
        result = dice(empty, single_voxel)
        assert result.value == pytest.approx(0.0)
        assert result.degeneracy is Degeneracy.PREDICTION_EMPTY

    def test_dice_is_zero_when_the_reference_is_empty(self, empty, single_voxel) -> None:
        result = dice(single_voxel, empty)
        assert result.value == pytest.approx(0.0)
        assert result.degeneracy is Degeneracy.REFERENCE_EMPTY

    @pytest.mark.parametrize("metric", [hd95, assd])
    def test_surface_metrics_refuse_rather_than_return_a_flattering_zero(
        self, metric, empty, single_voxel
    ) -> None:
        result = metric(empty, single_voxel, ISOTROPIC)
        assert result.value is None
        assert result.degeneracy is Degeneracy.PREDICTION_EMPTY
        assert "perfect boundary match" in result.detail

    def test_volume_error_keeps_the_sign_of_the_miss(self, empty, single_voxel) -> None:
        result = volume_error(empty, single_voxel, (10.0, 10.0, 10.0))
        assert result.signed_ml == pytest.approx(-1.0)
        assert result.degeneracy is Degeneracy.PREDICTION_EMPTY

    def test_relative_error_is_undefined_against_an_empty_reference(
        self, empty, single_voxel
    ) -> None:
        # Substituting a large number would rank this as the worst failure in the cohort
        # rather than as one that cannot be scored this way.
        result = volume_error(single_voxel, empty, ISOTROPIC)
        assert result.relative is None

    def test_surface_distances_raises_with_a_reason(self, empty, single_voxel) -> None:
        with pytest.raises(MetricError, match="undefined rather than large or zero"):
            surface_distances_mm(empty, single_voxel, ISOTROPIC)


class TestSingleVoxelAndDisjoint:
    def test_a_single_voxel_is_its_own_surface(self, single_voxel) -> None:
        assert assd(single_voxel, single_voxel, ISOTROPIC).value == pytest.approx(0.0)

    def test_disjoint_components_score_zero_dice_but_a_finite_distance(self) -> None:
        # Dice cannot distinguish "missed by one voxel" from "missed by half a head". HD95
        # can, which is why docs/10 requires both.
        prediction = np.zeros(SHAPE, dtype=bool)
        reference = np.zeros(SHAPE, dtype=bool)
        prediction[0, 0, 0] = True
        reference[4, 0, 0] = True
        assert dice(prediction, reference).value == pytest.approx(0.0)
        assert hd95(prediction, reference, ISOTROPIC).value == pytest.approx(4.0)


class TestCallerMistakes:
    def test_mismatched_shapes_are_an_error_not_a_score(self, single_voxel) -> None:
        with pytest.raises(MetricError, match="not the same case"):
            dice(single_voxel, np.zeros((5, 4, 4), dtype=bool))

    def test_a_two_dimensional_input_is_rejected(self) -> None:
        with pytest.raises(MetricError, match="3D volume"):
            dice(np.zeros((4, 4), dtype=bool), np.zeros((4, 4), dtype=bool))

    @pytest.mark.parametrize("spacing", [(0.0, 1.0, 1.0), (-1.0, 1.0, 1.0)])
    def test_a_zero_or_negative_spacing_is_rejected(self, single_voxel, spacing) -> None:
        # This is how a millimetre metric silently becomes a voxel count.
        with pytest.raises(MetricError, match="finite and positive"):
            hd95(single_voxel, single_voxel, spacing)

    def test_a_spacing_with_the_wrong_arity_is_rejected(self, single_voxel) -> None:
        with pytest.raises(MetricError, match="three components"):
            assd(single_voxel, single_voxel, (1.0, 1.0))


class TestAggregationCannotDropFailuresQuietly:
    def test_undefined_results_fail_loudly_under_the_fail_policy(
        self, empty, single_voxel
    ) -> None:
        results = [
            hd95(single_voxel, single_voxel, ISOTROPIC),
            hd95(empty, single_voxel, ISOTROPIC),
        ]
        with pytest.raises(ValueError, match="undefined and the policy is FAIL"):
            summarise(results, undefined=UndefinedPolicy.FAIL)

    def test_excluding_them_still_reports_how_many_were_excluded(
        self, empty, single_voxel
    ) -> None:
        # docs/10: silently dropping unprocessable cases inflates every number in the table
        # and is the easiest thing for an examiner to catch.
        results = [
            hd95(single_voxel, single_voxel, ISOTROPIC),
            hd95(empty, single_voxel, ISOTROPIC),
        ]
        summary = summarise(results, undefined=UndefinedPolicy.EXCLUDE)
        assert summary.n_total == 2
        assert summary.n_undefined == 1
        assert summary.n_used == 1
        assert summary.degeneracies == {"none": 1, "prediction-empty": 1}
        assert "1 undefined" in summary.as_table_cell()

    def test_the_policy_has_no_default(self) -> None:
        # A default would be a decision about how to report failures, made silently, in a
        # signature nobody reads.
        with pytest.raises(TypeError):
            summarise([dice(np.zeros(SHAPE), np.zeros(SHAPE))])  # type: ignore[call-arg]

    def test_mixing_two_metrics_in_one_summary_is_refused(self, single_voxel) -> None:
        with pytest.raises(ValueError, match="refusing to mix metrics"):
            summarise(
                [
                    dice(single_voxel, single_voxel),
                    assd(single_voxel, single_voxel, ISOTROPIC),
                ],
                undefined=UndefinedPolicy.EXCLUDE,
            )

    def test_an_empty_cohort_is_refused(self) -> None:
        with pytest.raises(ValueError, match="n is part of the answer"):
            summarise([], undefined=UndefinedPolicy.EXCLUDE)

    def test_median_and_iqr_over_a_known_set(self) -> None:
        """Dice values 0.2, 0.4, 0.6, 0.8, 1.0 by construction.

        numpy's linear-interpolation percentiles give median 0.6, q25 0.4, q75 0.8.
        """
        results = [
            dice(*_masks_scoring(numerator=n)) for n in (1, 2, 3, 4, 5)
        ]
        summary = summarise(results, undefined=UndefinedPolicy.EXCLUDE)
        assert summary.median == pytest.approx(0.6)
        assert summary.iqr_low == pytest.approx(0.4)
        assert summary.iqr_high == pytest.approx(0.8)
        assert summary.n_total == 5


def _masks_scoring(numerator: int) -> tuple[np.ndarray, np.ndarray]:
    """Two 5-voxel lines overlapping in ``numerator`` voxels, so Dice is ``numerator / 5``.

    |A| = |B| = 5, so Dice = 2 * overlap / 10 = overlap / 5.
    """
    prediction = np.zeros((16, 2, 2), dtype=bool)
    reference = np.zeros((16, 2, 2), dtype=bool)
    prediction[0:5, 0, 0] = True
    reference[5 - numerator : 10 - numerator, 0, 0] = True
    return prediction, reference
