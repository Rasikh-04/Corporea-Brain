"""Stage 3: the resample must change the grid and leave the anatomy where it was.

The orientation tests next door prove that reorientation preserves world coordinates. These
prove the harder half. Resampling genuinely changes the data — voxel counts move, boundaries
shift by up to half a voxel — so "nothing changed" is not the property to assert. The
property is that **the millimetres did not change while the voxels did**, and both halves of
that need testing: a stage that changed nothing at all would pass a world-coordinate check
while having silently skipped its job.
"""

from __future__ import annotations

import numpy as np
import pytest
from corporea_pipeline.orientation import Axis, OrientationError, Pole, voxel_sizes_mm
from corporea_pipeline.phantom import (
    BACKGROUND_INTENSITY,
    PHANTOM_MARKERS,
    PHANTOM_SPACING_MM,
    break_orientation,
    build_phantom,
    orientation_report,
)
from corporea_pipeline.resample import (
    Interpolation,
    ResampleError,
    output_grid,
    resample_to_grid,
    run_stage3,
    world_bounding_box,
)

ISOTROPIC_1MM = (1.0, 1.0, 1.0)
TARGET_CODES = ("L", "A", "S")


# --- The grid arithmetic, computed by hand -----------------------------------------------


@pytest.mark.known_answer
def test_output_grid_extent_is_hand_computable() -> None:
    """A 4x3x2 volume at 2 mm becomes 7x5x3 at 1 mm, and the origin does not move.

    By hand, along the first axis: the input spans voxel centres 0 to 3, which is
    ``3 * 2 = 6`` mm. At 1 mm that is ``6 / 1 = 6`` intervals, so ``6 + 1 = 7`` voxels. The
    same arithmetic gives ``2 * 2 / 1 + 1 = 5`` and ``1 * 2 / 1 + 1 = 3``.
    """
    affine = np.diag([2.0, 2.0, 2.0, 1.0])
    affine[:3, 3] = (-10.0, -20.0, -30.0)

    shape, target = output_grid((4, 3, 2), affine, ISOTROPIC_1MM)

    assert shape == (7, 5, 3)
    assert voxel_sizes_mm(target) == pytest.approx(ISOTROPIC_1MM)
    assert target[:3, 3] == pytest.approx((-10.0, -20.0, -30.0))


@pytest.mark.known_answer
def test_output_grid_rounds_the_extent_up_never_down() -> None:
    """3 voxels at 2 mm is 4 mm of span; at 3 mm that is 1.33 intervals, so 3 voxels, not 2.

    Rounding down would drop the far edge of the field of view, which is where a peripheral
    lesion sits and where over-stripping already costs volume.
    """
    affine = np.diag([2.0, 2.0, 2.0, 1.0])

    shape, _ = output_grid((3, 3, 3), affine, (3.0, 3.0, 3.0))

    assert shape == (3, 3, 3)


def test_resample_to_the_same_spacing_is_the_identity() -> None:
    phantom = build_phantom()

    data, affine = resample_to_grid(
        phantom.data,
        phantom.affine,
        spacing_mm=PHANTOM_SPACING_MM,
        interpolation=Interpolation.NEAREST,
    )

    assert data.shape == phantom.data.shape
    assert np.array_equal(data, phantom.data)
    assert affine == pytest.approx(phantom.affine)


def test_resample_preserves_the_integer_dtype_of_a_label_volume() -> None:
    """A label map that comes back as float is a label map that no longer compares equal."""
    phantom = build_phantom()

    data, _ = resample_to_grid(
        phantom.data,
        phantom.affine,
        spacing_mm=ISOTROPIC_1MM,
        interpolation=Interpolation.NEAREST,
    )

    assert data.dtype == phantom.data.dtype


# --- The world-space invariant ------------------------------------------------------------


@pytest.mark.orientation
def test_resample_changes_voxel_counts_and_not_world_centres() -> None:
    """Both halves at once: the voxels moved, the millimetres did not.

    The phantom is 1 x 1.25 x 2 mm. At 1 mm isotropic every marker gains voxels along j and
    k, by roughly 1.25x and 2x. If a marker's voxel count came back unchanged the resample
    did not happen, and the world-centre assertion below would be checking nothing.
    """
    phantom = build_phantom()

    result = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=TARGET_CODES,
        spacing_mm=ISOTROPIC_1MM,
        interpolation=Interpolation.NEAREST,
        markers=PHANTOM_MARKERS,
    )

    assert result.orientation is not None
    assert result.orientation.passed
    assert voxel_sizes_mm(result.affine) == pytest.approx(ISOTROPIC_1MM)

    counts_before = {marker.label: marker.expected_voxel_count for marker in PHANTOM_MARKERS}
    for check in result.orientation.checks:
        assert check.voxel_count > counts_before[check.label], (
            f"marker {check.label!r} kept {check.voxel_count} voxels through a resample from "
            f"{PHANTOM_SPACING_MM} mm to {ISOTROPIC_1MM} mm; the resample did not run"
        )

    expected_centres = {marker.label: marker.expected_centre_mm for marker in PHANTOM_MARKERS}
    for check in result.orientation.checks:
        assert check.centre.as_tuple() == pytest.approx(
            expected_centres[check.label].as_tuple(), abs=1.0
        )


@pytest.mark.orientation
@pytest.mark.parametrize(
    "target_codes",
    [("L", "A", "S"), ("R", "A", "S"), ("P", "I", "R"), ("A", "L", "S")],
)
def test_laterality_survives_every_target_orientation(
    target_codes: tuple[str, str, str],
) -> None:
    """The stage's answer must not depend on the voxel order it was asked to write.

    Four targets rather than all 48: the 48-order sweep is ``test_phantom_orientation.py``'s
    job on reorientation alone. What is new here is the resample running on top, and a fault
    in that composition shows up on the first non-identity order.
    """
    phantom = build_phantom()

    result = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=target_codes,
        spacing_mm=ISOTROPIC_1MM,
        interpolation=Interpolation.NEAREST,
        markers=PHANTOM_MARKERS,
    )

    assert result.orientation is not None
    assert result.orientation.passed, result.orientation.describe()
    assert "".join(result.record.target_axis_codes) == "".join(target_codes)


@pytest.mark.orientation
def test_the_world_bounding_box_is_not_cropped() -> None:
    phantom = build_phantom()
    low_before, high_before = world_bounding_box(phantom.data.shape, phantom.affine)

    result = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=TARGET_CODES,
        spacing_mm=ISOTROPIC_1MM,
        interpolation=Interpolation.NEAREST,
    )

    low_after, high_after = world_bounding_box(result.data.shape, result.affine)
    assert np.all(np.asarray(low_after.as_tuple()) <= np.asarray(low_before.as_tuple()) + 1e-6)
    assert np.all(np.asarray(high_after.as_tuple()) >= np.asarray(high_before.as_tuple()) - 1e-6)


@pytest.mark.orientation
def test_the_marker_free_path_makes_no_orientation_claim() -> None:
    """No markers means no orientation report. A ``None`` is honest; an empty pass is not."""
    phantom = build_phantom()

    result = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=TARGET_CODES,
        spacing_mm=ISOTROPIC_1MM,
        interpolation=Interpolation.NEAREST,
    )

    assert result.orientation is None


# --- The assertion has to be watched failing ----------------------------------------------


@pytest.mark.orientation
@pytest.mark.parametrize("voxel_axis", [0, 1, 2])
def test_stage3_rejects_a_volume_flipped_without_its_affine(voxel_axis: int) -> None:
    """The whole point. A flip upstream must not survive stage 3 unnoticed.

    ``break_orientation`` produces exactly the fixture that a voxel-index check passes and a
    world-space check fails, so this test is the one that says the check is the right kind.
    """
    phantom = build_phantom()
    broken_data, broken_affine = break_orientation(phantom.data, phantom.affine, voxel_axis)

    with pytest.raises(OrientationError):
        run_stage3(
            broken_data,
            broken_affine,
            target_axis_codes=TARGET_CODES,
            spacing_mm=ISOTROPIC_1MM,
            interpolation=Interpolation.NEAREST,
            markers=PHANTOM_MARKERS,
        )


@pytest.mark.orientation
def test_stage3_rejects_a_translated_volume_that_is_still_on_the_right_sides() -> None:
    """Laterality alone is not enough, so this is the case that proves the drift check runs.

    Shifting the volume 5 mm along +z leaves every marker on the pole it started on: the
    superior cap at ``z = +42`` goes to ``+47`` and is still superior, and the two markers on
    the other axes do not move along theirs at all. A check that only asked "is left still
    left" would pass it, and the lesion would then be reported 5 mm from where it is.
    """
    phantom = build_phantom()
    shifted = np.array(phantom.affine, dtype=np.float64)
    shifted[2, 3] += 5.0

    report = orientation_report(phantom.data, shifted)
    assert report.passed, "the shift must not itself flip a marker, or this proves nothing"

    with pytest.raises(OrientationError, match="moved marker anatomy"):
        run_stage3(
            phantom.data,
            shifted,
            target_axis_codes=TARGET_CODES,
            spacing_mm=ISOTROPIC_1MM,
            interpolation=Interpolation.NEAREST,
            markers=PHANTOM_MARKERS,
        )


@pytest.mark.orientation
def test_linear_interpolation_invents_labels_and_the_orientation_check_does_not_notice() -> None:
    """Why ``Interpolation`` has no default: nothing downstream catches the wrong choice.

    The expected story was that linear interpolation on a label volume would fail the
    orientation assertion. It does not, and that is the more useful fact. Linear blurs a
    marker's boundary symmetrically, so the exact-intensity core erodes evenly and its centre
    of mass stays put. Laterality survives. Every marker still passes.

    What actually happens is worse for being quiet. The blend produces intensities that are
    neither the background nor any marker — on this phantom, 121 values that are not a label
    at all — and it erodes each marker by roughly a third. Downstream, those are region
    boundaries that moved and voxels assigned to a class that does not exist, in a volume
    that passes every geometry check in the repository.

    So the guard cannot be a downstream assertion, because there is no downstream assertion
    that fires. It has to be at the call site, which is why ``Interpolation`` is a required
    keyword argument with no default.
    """
    phantom = build_phantom()
    labels = {0, BACKGROUND_INTENSITY} | {marker.intensity for marker in PHANTOM_MARKERS}
    fine = (0.7, 0.7, 0.7)

    nearest = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=TARGET_CODES,
        spacing_mm=fine,
        interpolation=Interpolation.NEAREST,
        markers=PHANTOM_MARKERS,
    )
    linear = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=TARGET_CODES,
        spacing_mm=fine,
        interpolation=Interpolation.LINEAR,
        markers=PHANTOM_MARKERS,
    )

    assert nearest.orientation is not None and nearest.orientation.passed
    assert linear.orientation is not None
    assert linear.orientation.passed, (
        "if this ever starts failing, the docstring above is out of date: the point of the "
        "test is that the orientation assertion does NOT catch a bad interpolation choice"
    )

    assert set(np.unique(nearest.data).tolist()) <= labels
    invented = set(np.unique(linear.data).tolist()) - labels
    assert len(invented) > 50, (
        "linear interpolation must be shown inventing values that are not any label; "
        f"found only {sorted(invented)}"
    )

    nearest_counts = {check.label: check.voxel_count for check in nearest.orientation.checks}
    for check in linear.orientation.checks:
        assert check.voxel_count < nearest_counts[check.label], (
            f"marker {check.label!r} did not erode under linear interpolation"
        )


# --- Refusals -----------------------------------------------------------------------------


@pytest.mark.parametrize("spacing", [(0.0, 1.0, 1.0), (-1.0, 1.0, 1.0), (float("nan"), 1.0, 1.0)])
def test_a_non_physical_spacing_is_refused(spacing: tuple[float, float, float]) -> None:
    phantom = build_phantom()

    with pytest.raises(ResampleError, match="positive and finite"):
        resample_to_grid(
            phantom.data,
            phantom.affine,
            spacing_mm=spacing,
            interpolation=Interpolation.NEAREST,
        )


def test_a_four_dimensional_series_is_refused_by_name() -> None:
    """The error has to say what to do, because the caller's next question is "then what"."""
    series = np.zeros((4, 4, 4, 3), dtype=np.uint8)

    with pytest.raises(ResampleError, match="4D series is split"):
        resample_to_grid(
            series,
            np.eye(4),
            spacing_mm=ISOTROPIC_1MM,
            interpolation=Interpolation.NEAREST,
        )


def test_a_singular_affine_is_refused() -> None:
    singular = np.diag([1.0, 1.0, 0.0, 1.0])

    with pytest.raises(ResampleError, match="singular"):
        resample_to_grid(
            np.zeros((4, 4, 4), dtype=np.uint8),
            singular,
            spacing_mm=ISOTROPIC_1MM,
            interpolation=Interpolation.NEAREST,
        )


# --- Provenance ----------------------------------------------------------------------------


def test_the_record_carries_both_affines_and_the_original_orientation_code() -> None:
    """``docs/06`` stage 3 asks for exactly this, and none of it is recoverable afterwards."""
    phantom = build_phantom()

    result = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=TARGET_CODES,
        spacing_mm=ISOTROPIC_1MM,
        interpolation=Interpolation.NEAREST,
    )
    record = result.record.as_dict()

    assert record["tool"] == "corporea_pipeline.resample"
    assert record["tool_version"]
    assert record["timestamp_utc"]
    assert record["interpolation"] == "nearest"
    assert record["source"]["axis_codes"] == "RAS"
    assert record["target"]["axis_codes"] == "LAS"
    assert record["source"]["spacing_mm"] == pytest.approx(list(PHANTOM_SPACING_MM))
    assert record["target"]["spacing_mm"] == pytest.approx(list(ISOTROPIC_1MM))
    assert np.asarray(record["source"]["affine"]).shape == (4, 4)
    assert np.asarray(record["target"]["affine"]).shape == (4, 4)
    # RAS is right-handed and LAS is left-handed, so the sign legitimately flips here. Both
    # are recorded rather than reduced to a verdict, because the sign is only interpretable
    # next to the orientation code it belongs to.
    assert record["source"]["determinant_sign"] == 1
    assert record["target"]["determinant_sign"] == -1


def test_the_record_serialises_to_json_without_numpy() -> None:
    """A provenance sidecar that needs numpy to read is a sidecar nobody reads."""
    import json

    phantom = build_phantom()
    result = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=TARGET_CODES,
        spacing_mm=ISOTROPIC_1MM,
        interpolation=Interpolation.NEAREST,
    )

    round_tripped = json.loads(json.dumps(result.record.as_dict()))

    assert round_tripped["target"]["shape"] == list(result.data.shape)


def test_a_named_marker_reports_the_side_it_is_on() -> None:
    """A sanity anchor for the parametrised cases above: LAS still puts left on the left."""
    phantom = build_phantom()

    result = run_stage3(
        phantom.data,
        phantom.affine,
        target_axis_codes=TARGET_CODES,
        spacing_mm=ISOTROPIC_1MM,
        interpolation=Interpolation.NEAREST,
        markers=PHANTOM_MARKERS,
    )

    assert result.orientation is not None
    lateral = [check for check in result.orientation.checks if check.axis is Axis.LEFT_RIGHT]
    assert lateral, "the phantom must carry at least one left/right marker"
    assert all(check.observed in (Pole.LEFT, Pole.RIGHT) for check in lateral)
    assert all(check.passed for check in lateral)
