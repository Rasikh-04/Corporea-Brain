"""Known-answer tests. Every expected value below was computed by hand.

``docs/10-EVALUATION_PROTOCOL.md``: the known-answer test is the single highest-value test in
the repository. ``docs/16-TESTING_STRATEGY.md`` puts it in the commit-level gate beside the
orientation assertion, for the same reason: a broken metric is silent, and it produces
plausible numbers that get transcribed into a results table and defended at a viva.

The arithmetic is in each docstring. If one of these fails, redo the arithmetic. Do not paste
in what the code printed: that converts the only independent check on the metrics into a
restatement of the implementation.
"""

from __future__ import annotations

import numpy as np
import pytest

from braintwin_eval.metrics import assd, dice, hd95, volume_error

pytestmark = pytest.mark.known_answer

ISOTROPIC = (1.0, 1.0, 1.0)


def box(shape, i, j, k) -> np.ndarray:
    """A boolean volume with one filled box. Half-open ranges."""
    volume = np.zeros(shape, dtype=bool)
    volume[i[0] : i[1], j[0] : j[1], k[0] : k[1]] = True
    return volume


class TestDice:
    def test_identical_masks_score_one(self) -> None:
        mask = box((6, 4, 4), (0, 3), (0, 3), (0, 3))
        assert dice(mask, mask).value == pytest.approx(1.0)

    def test_disjoint_masks_score_zero(self) -> None:
        prediction = box((8, 4, 4), (0, 2), (0, 2), (0, 2))
        reference = box((8, 4, 4), (5, 7), (0, 2), (0, 2))
        assert dice(prediction, reference).value == pytest.approx(0.0)

    def test_cube_shifted_by_one_voxel(self) -> None:
        """Two 3x3x3 cubes offset by one along i.

        |A| = 27, |B| = 27. The overlap is i in {1, 2} by 3 by 3 = 18 voxels.
        Dice = 2 * 18 / (27 + 27) = 36 / 54 = 2/3.
        """
        prediction = box((6, 4, 4), (0, 3), (0, 3), (0, 3))
        reference = box((6, 4, 4), (1, 4), (0, 3), (0, 3))
        assert dice(prediction, reference).value == pytest.approx(2.0 / 3.0)

    def test_prediction_entirely_inside_reference(self) -> None:
        """A 2x2x2 prediction inside a 3x3x3 reference.

        |A| = 8, |B| = 27, overlap = 8. Dice = 2 * 8 / (8 + 27) = 16 / 35.

        Worth having explicitly: a perfectly placed prediction that misses no boundary and
        makes no false positive still scores 0.457 because it under-segments. This is the
        arithmetic behind the small-lesion warning in docs/10.
        """
        prediction = box((6, 4, 4), (0, 2), (0, 2), (0, 2))
        reference = box((6, 4, 4), (0, 3), (0, 3), (0, 3))
        assert dice(prediction, reference).value == pytest.approx(16.0 / 35.0)

    def test_dice_is_symmetric(self) -> None:
        prediction = box((6, 4, 4), (0, 2), (0, 2), (0, 2))
        reference = box((6, 4, 4), (0, 3), (0, 3), (0, 3))
        assert dice(prediction, reference).value == dice(reference, prediction).value


class TestSurfaceDistances:
    def test_identical_masks_have_zero_distance(self) -> None:
        mask = box((8, 6, 6), (2, 5), (2, 5), (2, 5))
        assert hd95(mask, mask, ISOTROPIC).value == pytest.approx(0.0)
        assert assd(mask, mask, ISOTROPIC).value == pytest.approx(0.0)

    def test_two_single_voxels_three_apart(self) -> None:
        """One voxel at (0,0,0) against one at (3,0,0), isotropic 1 mm.

        Each mask is its own surface. Both directed distance sets are [3.0], so
        HD95 = max(3, 3) = 3.0 and ASSD = (3 + 3) / (1 + 1) = 3.0.
        """
        prediction = box((6, 3, 3), (0, 1), (0, 1), (0, 1))
        reference = box((6, 3, 3), (3, 4), (0, 1), (0, 1))
        assert hd95(prediction, reference, ISOTROPIC).value == pytest.approx(3.0)
        assert assd(prediction, reference, ISOTROPIC).value == pytest.approx(3.0)

    def test_assd_pools_the_surfaces_rather_than_averaging_two_means(self) -> None:
        """Prediction {(0,0,0)}; reference {(0,0,0), (3,0,0)}; isotropic 1 mm.

        Surfaces: the prediction is one voxel; both reference voxels are surface, since each
        has a background neighbour.

        d(pred -> ref) = [0.0]                  because (0,0,0) is in the reference too
        d(ref -> pred) = [0.0, 3.0]

        ASSD pools:            (0 + 0 + 3) / (1 + 2) = 1.0
        Averaging two means would give: (0 + 1.5) / 2 = 0.75

        The two differ whenever the surfaces are different sizes, so this test pins which one
        this module implements.
        """
        prediction = box((6, 3, 3), (0, 1), (0, 1), (0, 1))
        reference = np.zeros((6, 3, 3), dtype=bool)
        reference[0, 0, 0] = True
        reference[3, 0, 0] = True
        assert assd(prediction, reference, ISOTROPIC).value == pytest.approx(1.0)

    def test_hd95_takes_the_worse_of_the_two_directions(self) -> None:
        """Same masks as above.

        p95([0.0]) = 0.0. p95([0.0, 3.0]) with numpy's linear interpolation is
        0 + 0.95 * (3 - 0) = 2.85. HD95 = max(0.0, 2.85) = 2.85.

        Pins both the symmetric form and the percentile convention, which vary in the
        literature and must be stated in the thesis.
        """
        prediction = box((6, 3, 3), (0, 1), (0, 1), (0, 1))
        reference = np.zeros((6, 3, 3), dtype=bool)
        reference[0, 0, 0] = True
        reference[3, 0, 0] = True
        assert hd95(prediction, reference, ISOTROPIC).value == pytest.approx(2.85)

    def test_distances_are_millimetres_and_not_voxels(self) -> None:
        """One voxel at (0,0,0) against one at (0,0,2), spacing (1, 1, 5) mm.

        Two voxels apart along k, at 5 mm per voxel, is 10 mm. A metric that dropped the
        spacing would report 2.0 and would be wrong by the anisotropy ratio on every clinical
        acquisition, which are routinely 5 mm through-plane against 1 mm in-plane.
        """
        prediction = box((3, 3, 6), (0, 1), (0, 1), (0, 1))
        reference = box((3, 3, 6), (0, 1), (0, 1), (2, 3))
        assert hd95(prediction, reference, (1.0, 1.0, 5.0)).value == pytest.approx(10.0)
        assert assd(prediction, reference, (1.0, 1.0, 5.0)).value == pytest.approx(10.0)

    def test_a_hollow_interior_is_not_surface(self) -> None:
        """A 3x3x3 cube has 27 voxels and 26 surface voxels: only the centre is interior.

        Checked through ASSD against a copy of itself missing the centre voxel. Both have the
        same 26-voxel surface, so every distance is zero.
        """
        solid = box((7, 7, 7), (2, 5), (2, 5), (2, 5))
        hollow = solid.copy()
        hollow[3, 3, 3] = False
        assert assd(solid, hollow, ISOTROPIC).value == pytest.approx(0.0)
        assert hd95(solid, hollow, ISOTROPIC).value == pytest.approx(0.0)


class TestVolumeError:
    def test_volumes_in_millilitres_at_one_millilitre_per_voxel(self) -> None:
        """Spacing (10, 10, 10) mm gives 1000 mm3 per voxel, which is exactly 1 ml.

        Prediction 27 voxels = 27 ml, reference 8 voxels = 8 ml.
        signed = 27 - 8 = +19 ml, absolute = 19 ml, relative = 19 / 8 = 2.375.
        """
        prediction = box((6, 4, 4), (0, 3), (0, 3), (0, 3))
        reference = box((6, 4, 4), (0, 2), (0, 2), (0, 2))
        result = volume_error(prediction, reference, (10.0, 10.0, 10.0))

        assert result.prediction_ml == pytest.approx(27.0)
        assert result.reference_ml == pytest.approx(8.0)
        assert result.signed_ml == pytest.approx(19.0)
        assert result.absolute_ml == pytest.approx(19.0)
        assert result.relative == pytest.approx(2.375)

    def test_under_segmentation_is_signed_negative(self) -> None:
        # The sign is kept because docs/10 requires Bland-Altman with limits of agreement,
        # and an unsigned error cannot produce one.
        prediction = box((6, 4, 4), (0, 2), (0, 2), (0, 2))
        reference = box((6, 4, 4), (0, 3), (0, 3), (0, 3))
        result = volume_error(prediction, reference, (10.0, 10.0, 10.0))
        assert result.signed_ml == pytest.approx(-19.0)
        assert result.absolute_ml == pytest.approx(19.0)

    def test_anisotropic_voxel_volume(self) -> None:
        """Spacing (2, 2.5, 4) mm is 20 mm3 per voxel. 8 voxels is 160 mm3 = 0.16 ml."""
        mask = box((6, 4, 4), (0, 2), (0, 2), (0, 2))
        empty = np.zeros((6, 4, 4), dtype=bool)
        result = volume_error(mask, empty, (2.0, 2.5, 4.0))
        assert result.prediction_ml == pytest.approx(0.16)
