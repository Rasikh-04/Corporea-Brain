"""The orientation assertion. The most important test in the repository.

``docs/16-TESTING_STRATEGY.md`` puts this in the commit-level gate and says never to bypass
it. ``docs/06-IMAGING_PIPELINE.md`` explains why: a left/right flip anywhere in the chain puts
the lesion in the wrong hemisphere, and attribution, tracts, deficit hypotheses and the
proximity warning are then all confidently wrong while the images look completely normal.

Nothing here may be marked ``skip`` or ``xfail``. If one of these fails, the pipeline has no
valid output and the fix is the pipeline, never the test.
"""

from __future__ import annotations

import itertools

import numpy as np
import pytest

from braintwin_pipeline.orientation import (
    Axis,
    OrientationError,
    Pole,
    assert_no_flip,
    determinant_sign,
)
from braintwin_pipeline.phantom import (
    PHANTOM_MARKERS,
    PHANTOM_SHAPE,
    PHANTOM_SPACING_MM,
    break_orientation,
    build_phantom,
    orientation_report,
    reorient,
)

pytestmark = pytest.mark.orientation


def all_axis_codes() -> list[tuple[str, str, str]]:
    """Every one of the 48 ways a volume can be written down: 6 orders times 8 sign choices."""
    poles = (("R", "L"), ("A", "P"), ("S", "I"))
    return [
        tuple(poles[order[n]][signs[n]] for n in range(3))
        for order in itertools.permutations(range(3))
        for signs in itertools.product((0, 1), repeat=3)
    ]


@pytest.fixture(scope="module")
def phantom():
    return build_phantom()


class TestPhantomGrid:
    """The grid's awkwardness is the point. These guard it against being tidied up."""

    def test_no_two_dimensions_are_equal(self) -> None:
        # Equal dimensions let an axis transpose pass through with nothing observably
        # different about the array.
        assert len(set(PHANTOM_SHAPE)) == 3

    def test_no_two_voxel_spacings_are_equal(self) -> None:
        # Isotropic spacing hides the same bug one level down: transpose the columns of an
        # isotropic direction matrix and it is unchanged.
        assert len(set(PHANTOM_SPACING_MM)) == 3

    def test_the_volume_centre_is_nowhere_near_the_world_origin(self, phantom) -> None:
        # A phantom whose middle sits at (0, 0, 0) is symmetric under negation of the affine's
        # translation column, which is one of the ways a sign error hides.
        middle_voxel = (np.array(PHANTOM_SHAPE) - 1) / 2.0
        world_centre = phantom.affine[:3, :3] @ middle_voxel + phantom.affine[:3, 3]
        assert np.all(np.abs(world_centre) > 1.0), world_centre

    def test_every_marker_has_a_unique_intensity(self) -> None:
        intensities = [marker.intensity for marker in PHANTOM_MARKERS]
        assert len(set(intensities)) == len(intensities)

    def test_the_three_markers_cover_three_different_axes(self) -> None:
        # One marker leaves two axes unguarded, and a superior/inferior flip invalidates a
        # result just as completely as a left/right one while attracting less suspicion.
        assert {marker.axis for marker in PHANTOM_MARKERS} == set(Axis)

    def test_the_phantom_is_read_only(self, phantom) -> None:
        with pytest.raises(ValueError):
            phantom.data[0, 0, 0] = 1

    def test_two_builds_are_bit_identical(self) -> None:
        # No random number generator, no seed, no machine dependence. This is what lets the
        # expected centres below be constants instead of tolerances.
        first, second = build_phantom(), build_phantom()
        assert np.array_equal(first.data, second.data)
        assert np.array_equal(first.affine, second.affine)


@pytest.mark.known_answer
class TestMarkersLandWhereTheyWereHandComputed:
    """Against arithmetic worked out on paper, not against what the code printed once.

    The derivation for each marker is in the comments above ``PHANTOM_MARKERS``. If one of
    these fails, redo that arithmetic. Pasting in the observed value turns the only
    independent check in the phantom into a tautology.
    """

    @pytest.mark.parametrize("marker", PHANTOM_MARKERS, ids=lambda m: m.label)
    def test_centre_of_mass_matches_the_hand_computed_millimetres(
        self, phantom, marker
    ) -> None:
        check = next(
            c for c in orientation_report(phantom.data, phantom.affine).checks
            if c.label == marker.label
        )
        assert check.centre.as_tuple() == pytest.approx(
            marker.expected_centre_mm.as_tuple()
        )

    @pytest.mark.parametrize("marker", PHANTOM_MARKERS, ids=lambda m: m.label)
    def test_voxel_count_matches_the_box_volume(self, phantom, marker) -> None:
        # Guards against a marker being clipped at an array edge, which would move its centre
        # of mass by an amount too small to look wrong.
        assert int((phantom.data == marker.intensity).sum()) == marker.expected_voxel_count


class TestCanonicalPhantom:
    def test_every_marker_is_on_the_side_it_claims(self, phantom) -> None:
        report = orientation_report(phantom.data, phantom.affine)
        assert report.passed, report.describe()

    def test_the_report_carries_what_the_qc_panel_needs(self, phantom) -> None:
        # docs/06: the orientation panel shows the code before and after, and the determinant
        # sign. A verdict with no evidence sends the reader back to the data.
        report = orientation_report(phantom.data, phantom.affine)
        assert report.axis_codes == ("R", "A", "S")
        assert report.determinant_sign == 1
        assert report.voxel_sizes_mm == pytest.approx(PHANTOM_SPACING_MM)
        assert len(report.checks) == len(PHANTOM_MARKERS)

    def test_assert_no_flip_returns_the_report_so_it_can_be_logged(self, phantom) -> None:
        report = orientation_report(phantom.data, phantom.affine)
        assert assert_no_flip(report) is report


class TestReorientationPreservesTheObject:
    """A correct reorientation moves voxel indices and moves nothing in the patient."""

    @pytest.mark.parametrize("codes", all_axis_codes(), ids=lambda c: "".join(c))
    def test_all_48_storage_orders_report_identically(self, phantom, codes) -> None:
        moved_data, moved_affine = reorient(phantom.data, phantom.affine, codes)
        report = orientation_report(moved_data, moved_affine)

        assert report.passed, f"{''.join(codes)}\n{report.describe()}"
        assert report.axis_codes == codes

        canonical = {c.label: c for c in orientation_report(phantom.data, phantom.affine).checks}
        for check in report.checks:
            assert check.centre.as_tuple() == pytest.approx(
                canonical[check.label].centre.as_tuple()
            ), f"{check.label} moved in the patient when only its storage order changed"
            assert check.voxel_count == canonical[check.label].voxel_count

    def test_voxel_indices_really_do_move(self, phantom) -> None:
        # Without this the test above would also pass on a reorient that did nothing at all.
        moved_data, _ = reorient(phantom.data, phantom.affine, ("L", "A", "S"))
        assert not np.array_equal(moved_data, phantom.data)


class TestABrokenOrientationIsCaught:
    """The fixture ``docs/06`` asks for: break it on purpose and watch how invisible it is.

    An assertion nobody has seen fail is not known to work, and this one guards a failure mode
    with no symptom of its own.
    """

    @pytest.mark.parametrize(
        ("voxel_axis", "label", "expected_wrong_pole"),
        [
            (0, "left-block", Pole.RIGHT),
            (1, "anterior-wedge", Pole.POSTERIOR),
            (2, "superior-cap", Pole.INFERIOR),
        ],
    )
    def test_a_flip_without_the_affine_update_fails_the_assertion(
        self, phantom, voxel_axis, label, expected_wrong_pole
    ) -> None:
        broken_data, broken_affine = break_orientation(
            phantom.data, phantom.affine, voxel_axis
        )
        report = orientation_report(broken_data, broken_affine)

        assert not report.passed
        assert [failure.label for failure in report.failures] == [label]
        assert report.failures[0].observed is expected_wrong_pole

        with pytest.raises(OrientationError, match="wrong hemisphere"):
            assert_no_flip(report)

    def test_a_missing_marker_names_the_right_cause(self, phantom) -> None:
        # A marker that an interpolating resample erased is gone, not on the wrong side, and
        # reporting it as the latter would send the next person to the wrong stage.
        erased = np.asarray(phantom.data).copy()
        erased[erased == PHANTOM_MARKERS[0].intensity] = 0
        with pytest.raises(OrientationError, match="it is gone"):
            orientation_report(erased, phantom.affine)


class TestWhyTheAssertionIsMadeInWorldSpace:
    """The single idea this module exists to encode, written as a test.

    A correct reorientation to LAS and a broken flip along i produce **the same array**. They
    differ only in the affine. Any check that reads voxel indices cannot tell them apart: it
    fails on the correct operation and passes on the catastrophic one.
    """

    @staticmethod
    @pytest.fixture(scope="class")
    def correct_and_broken(phantom):
        correct = reorient(phantom.data, phantom.affine, ("L", "A", "S"))
        broken = break_orientation(phantom.data, phantom.affine, 0)
        return correct, broken

    def test_the_voxel_data_is_byte_identical(self, correct_and_broken) -> None:
        (correct_data, _), (broken_data, _) = correct_and_broken
        assert np.array_equal(correct_data, broken_data)

    def test_only_the_affine_differs(self, correct_and_broken) -> None:
        (_, correct_affine), (_, broken_affine) = correct_and_broken
        assert not np.array_equal(correct_affine, broken_affine)

    def test_the_world_space_assertion_separates_them(self, correct_and_broken) -> None:
        (correct_data, correct_affine), (broken_data, broken_affine) = correct_and_broken
        assert orientation_report(correct_data, correct_affine).passed
        assert not orientation_report(broken_data, broken_affine).passed

    def test_the_determinant_sign_changes_on_the_correct_one_and_not_the_broken_one(
        self, phantom, correct_and_broken
    ) -> None:
        # Worth knowing before anyone proposes the determinant sign as a cheaper check. It
        # moves on the safe operation and sits still through the fatal one, which is exactly
        # backwards from the intuition that suggests it.
        (_, correct_affine), (_, broken_affine) = correct_and_broken
        canonical_sign = determinant_sign(phantom.affine)
        assert determinant_sign(correct_affine) == -canonical_sign
        assert determinant_sign(broken_affine) == canonical_sign
