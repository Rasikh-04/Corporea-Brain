"""Unit tests for the orientation primitives.

The assertion these support is tested in ``test_phantom_orientation.py``. This file covers the
arithmetic underneath it, including the cases where the honest answer is a refusal.
"""

from __future__ import annotations

import numpy as np
import pytest
from braintwin_pipeline.orientation import (
    Axis,
    OrientationError,
    Pole,
    WorldPoint,
    axis_codes,
    determinant_sign,
    mask_centre_of_world,
    pole_of,
    voxel_sizes_mm,
    voxel_to_world,
)

# i toward the patient's right at 2 mm, j anterior at 3 mm, k superior at 4 mm, origin
# (-10, -20, -30). Every number distinct so a transposed row or column cannot pass.
AFFINE = np.array(
    [
        [2.0, 0.0, 0.0, -10.0],
        [0.0, 3.0, 0.0, -20.0],
        [0.0, 0.0, 4.0, -30.0],
        [0.0, 0.0, 0.0, 1.0],
    ]
)


class TestVoxelToWorld:
    def test_origin_voxel_maps_to_the_affine_translation(self) -> None:
        assert voxel_to_world(AFFINE, (0, 0, 0)) == WorldPoint(-10.0, -20.0, -30.0)

    def test_applies_spacing_per_axis(self) -> None:
        # (5, 10, 15) -> (5*2 - 10, 10*3 - 20, 15*4 - 30) = (0, 10, 30)
        assert voxel_to_world(AFFINE, (5, 10, 15)) == WorldPoint(0.0, 10.0, 30.0)

    def test_accepts_fractional_indices(self) -> None:
        # A centre of mass lands between voxels far more often than on one.
        assert voxel_to_world(AFFINE, (0.5, 0.5, 0.5)) == WorldPoint(-9.0, -18.5, -28.0)

    @pytest.mark.parametrize("bad", [np.eye(3), np.zeros((4, 3)), np.eye(5)])
    def test_rejects_an_affine_that_is_not_four_by_four(self, bad: np.ndarray) -> None:
        with pytest.raises(ValueError, match="must be 4x4"):
            voxel_to_world(bad, (0, 0, 0))

    def test_rejects_a_non_finite_affine(self) -> None:
        broken = AFFINE.copy()
        broken[0, 3] = np.nan
        with pytest.raises(ValueError, match="non-finite"):
            voxel_to_world(broken, (0, 0, 0))


class TestMaskCentreOfWorld:
    def test_single_voxel_mask_centres_on_that_voxel(self) -> None:
        mask = np.zeros((4, 4, 4), dtype=bool)
        mask[1, 2, 3] = True
        assert mask_centre_of_world(mask, AFFINE) == voxel_to_world(AFFINE, (1, 2, 3))

    def test_centre_is_the_unweighted_mean_of_voxel_indices(self) -> None:
        # Voxels i=1 and i=3 at fixed j, k. Mean i is 2, so x = 2*2 - 10 = -6.
        mask = np.zeros((5, 5, 5), dtype=bool)
        mask[1, 0, 0] = True
        mask[3, 0, 0] = True
        assert mask_centre_of_world(mask, AFFINE).x == pytest.approx(-6.0)

    def test_empty_mask_refuses_rather_than_returning_the_origin(self) -> None:
        # Returning WorldPoint(0, 0, 0) here would read downstream as a real measurement of a
        # structure at the world origin, which is roughly the middle of the head.
        with pytest.raises(OrientationError, match="no centre of mass"):
            mask_centre_of_world(np.zeros((3, 3, 3), dtype=bool), AFFINE)


class TestAffineDescriptors:
    def test_axis_codes_of_a_ras_affine(self) -> None:
        assert axis_codes(AFFINE) == ("R", "A", "S")

    def test_axis_codes_follow_a_flipped_column(self) -> None:
        flipped = AFFINE.copy()
        flipped[0, 0] = -2.0
        assert axis_codes(flipped) == ("L", "A", "S")

    def test_determinant_sign_is_positive_for_a_right_handed_affine(self) -> None:
        assert determinant_sign(AFFINE) == 1

    def test_determinant_sign_flips_with_a_single_axis(self) -> None:
        flipped = AFFINE.copy()
        flipped[0, 0] = -2.0
        assert determinant_sign(flipped) == -1

    def test_determinant_sign_refuses_a_singular_direction_matrix(self) -> None:
        singular = AFFINE.copy()
        singular[2, 2] = 0.0
        with pytest.raises(OrientationError, match="singular"):
            determinant_sign(singular)

    def test_voxel_sizes_are_the_column_norms(self) -> None:
        assert voxel_sizes_mm(AFFINE) == pytest.approx((2.0, 3.0, 4.0))

    def test_voxel_sizes_survive_a_rotated_affine(self) -> None:
        # A 90 degree rotation in the x-y plane at 2 mm and 3 mm spacing. The sizes are a
        # property of the geometry, not of which axis happens to be near which.
        rotated = np.eye(4)
        rotated[:3, :3] = np.array([[0.0, -3.0, 0.0], [2.0, 0.0, 0.0], [0.0, 0.0, 4.0]])
        assert voxel_sizes_mm(rotated) == pytest.approx((2.0, 3.0, 4.0))


class TestPoleOf:
    @pytest.mark.parametrize(
        ("point", "axis", "expected"),
        [
            (WorldPoint(-30.0, 0.0, 0.0), Axis.LEFT_RIGHT, Pole.LEFT),
            (WorldPoint(30.0, 0.0, 0.0), Axis.LEFT_RIGHT, Pole.RIGHT),
            (WorldPoint(0.0, -30.0, 0.0), Axis.POSTERIOR_ANTERIOR, Pole.POSTERIOR),
            (WorldPoint(0.0, 30.0, 0.0), Axis.POSTERIOR_ANTERIOR, Pole.ANTERIOR),
            (WorldPoint(0.0, 0.0, -30.0), Axis.INFERIOR_SUPERIOR, Pole.INFERIOR),
            (WorldPoint(0.0, 0.0, 30.0), Axis.INFERIOR_SUPERIOR, Pole.SUPERIOR),
        ],
    )
    def test_sign_selects_the_pole(self, point: WorldPoint, axis: Axis, expected: Pole) -> None:
        assert pole_of(point, axis) is expected

    def test_exact_zero_is_the_neutral_plane_and_not_a_coin_toss(self) -> None:
        # The one that matters. Reporting a midline structure as left because the sign bit
        # fell that way is the silent guess this whole module exists to prevent.
        assert pole_of(WorldPoint(0.0, 0.0, 0.0), Axis.LEFT_RIGHT) is Pole.MIDLINE

    def test_negative_zero_is_also_the_neutral_plane(self) -> None:
        assert pole_of(WorldPoint(-0.0, 0.0, 0.0), Axis.LEFT_RIGHT) is Pole.MIDLINE

    @pytest.mark.parametrize(
        ("axis", "neutral"),
        [
            (Axis.LEFT_RIGHT, Pole.MIDLINE),
            (Axis.POSTERIOR_ANTERIOR, Pole.MID_CORONAL),
            (Axis.INFERIOR_SUPERIOR, Pole.MID_AXIAL),
        ],
    )
    def test_each_axis_has_its_own_neutral_plane(self, axis: Axis, neutral: Pole) -> None:
        assert pole_of(WorldPoint(0.0, 0.0, 0.0), axis) is neutral

    def test_within_tolerance_is_neutral_and_just_outside_it_is_not(self) -> None:
        just_inside = WorldPoint(0.9, 0.0, 0.0)
        just_outside = WorldPoint(1.1, 0.0, 0.0)
        assert pole_of(just_inside, Axis.LEFT_RIGHT, tolerance_mm=1.0) is Pole.MIDLINE
        assert pole_of(just_outside, Axis.LEFT_RIGHT, tolerance_mm=1.0) is Pole.RIGHT

    def test_tolerance_boundary_is_inclusive(self) -> None:
        assert pole_of(WorldPoint(1.0, 0.0, 0.0), Axis.LEFT_RIGHT, tolerance_mm=1.0) is (
            Pole.MIDLINE
        )

    def test_negative_tolerance_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="must not be negative"):
            pole_of(WorldPoint(1.0, 0.0, 0.0), Axis.LEFT_RIGHT, tolerance_mm=-1.0)
