"""Slicer-side driver for the instructor demonstration.

Run by ``demo/run-demo.sh`` as ``Slicer --python-script demo/slicer/driver.py``. It keeps one
Slicer window open for the whole demonstration and changes what it shows when the terminal
asks, so stepping forward or back never waits for the application to restart.

The channel is two files in ``build/demo-state/``, both git-ignored:

- ``control`` is written by the terminal: ``<sequence number> <act name>``.
- ``status`` is written here: ``<sequence number> ok|error`` then one line per fact to print.

A file channel rather than Slicer's web server, because the web server's exec endpoint is a
remote code execution surface and a demonstration does not need one.

Everything this file shows is one of three things, and every act says which:

- **platform**: stock 3D Slicer tools, used as supplied. Not our work.
- **ours**: output of code in this repository.
- **mock**: synthetic data with made-up region names, showing the shape of a result we have
  not built yet. Never anatomy, never a finding.

Rule 2 applies to the captions as much as to the product: no act names a pathology, a region
or a diagnosis. The public scans are described by the sample name the Slicer project gave them
and by nothing else.
"""

from __future__ import annotations

import os
import time
import traceback
from collections.abc import Callable

import numpy as np
import qt
import slicer
import vtk

ROOT = os.environ["CORPOREA_DEMO_ROOT"]
STATE = os.environ["CORPOREA_DEMO_STATE"]
SHOTS = os.environ.get("CORPOREA_DEMO_SHOTS", "")
DATA = os.path.join(ROOT, "build", "demo-data")

POLL_INTERVAL_MS = 200
RENDER_TIMING_FRAMES = 30
# The left marker of the orientation phantom, in world millimetres. Copied from
# pipeline/corporea_pipeline/phantom.py (PHANTOM_MARKERS) so the views open on the slice that
# contains it. The act recomputes the centre from the voxels and does not trust this value.
PHANTOM_LEFT_MARKER_MM = (-16.0, 2.5, 8.0)
PHANTOM_LEFT_MARKER_LABEL = 200
PHANTOM_ZOOM_OUT = 1.6
# A voxel inside the bright region of the MRBrainTumor1 sample, found by inspection. It is
# valid for that exact file only, which demo/fetch-data.sh pins by SHA-256.
SEED_IJK = (128, 92, 77)
SEED_MULTIPLIERS = (2.0, 2.5, 3.0)
SEED_MULTIPLIER_SHOWN = 2.5
MOCK_SHAPE = (96, 96, 96)
MOCK_LESION_CENTRE = (40, 52, 50)
MOCK_LESION_RADIUS = 17

LAYOUT = slicer.vtkMRMLLayoutNode


def _layout(layout_id: int) -> None:
    slicer.app.layoutManager().setLayout(layout_id)


def _caption(text: str) -> None:
    """Say on screen what is being shown, so a photo of the projector is self-describing."""
    slicer.util.showStatusMessage(text)
    manager = slicer.app.layoutManager()
    for index in range(manager.threeDViewCount):
        view = manager.threeDWidget(index).threeDView()
        view.cornerAnnotation().SetText(vtk.vtkCornerAnnotation.UpperRight, text)
        view.cornerAnnotation().GetTextProperty().SetColor(1.0, 1.0, 1.0)


def _reset_scene() -> None:
    slicer.mrmlScene.Clear(False)
    for name in ("Red", "Yellow", "Green"):
        slicer.app.layoutManager().sliceWidget(name).mrmlSliceNode().SetSliceVisible(False)


def _load(filename: str, name: str) -> slicer.vtkMRMLScalarVolumeNode:
    path = os.path.join(DATA, filename)
    if not os.path.exists(path):
        raise FileNotFoundError(f"{path} is missing. Run demo/fetch-data.sh while online.")
    return slicer.util.loadVolume(path, {"name": name, "show": False})


def _geometry(node: slicer.vtkMRMLScalarVolumeNode) -> str:
    dims = node.GetImageData().GetDimensions()
    spacing = node.GetSpacing()
    return (
        f"{dims[0]} x {dims[1]} x {dims[2]} voxels at "
        f"{spacing[0]:.2f} x {spacing[1]:.2f} x {spacing[2]:.2f} mm"
    )


def _show_in_slices(node: slicer.vtkMRMLScalarVolumeNode, views: tuple[str, ...]) -> None:
    manager = slicer.app.layoutManager()
    for name in views:
        widget = manager.sliceWidget(name)
        widget.sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(node.GetID())
        widget.sliceLogic().FitSliceToAll()


def _orientation_marker(views: tuple[str, ...]) -> None:
    for name in views:
        view_node = slicer.app.layoutManager().sliceWidget(name).mrmlSliceNode()
        view_node.SetOrientationMarkerType(slicer.vtkMRMLAbstractViewNode.OrientationMarkerTypeAxes)


def _reset_camera() -> None:
    view = slicer.app.layoutManager().threeDWidget(0).threeDView()
    view.resetFocalPoint()
    view.resetCamera()


def act_platform() -> list[str]:
    """platform: ask the running application what it is, and count what it loaded."""
    _reset_scene()
    _layout(LAYOUT.SlicerLayoutFourUpView)
    slicer.util.selectModule("Welcome")
    manager = slicer.app.moduleManager()
    counts = {"CLI": 0, "loadable": 0, "scripted": 0}
    for name in manager.modulesNames():
        class_name = manager.module(name).className()
        if class_name == "qSlicerCLIModule":
            counts["CLI"] += 1
        elif class_name == "qSlicerScriptedLoadableModule":
            counts["scripted"] += 1
        else:
            counts["loadable"] += 1
    total = len(manager.modulesNames())
    _caption("3D Slicer, built from source on this laptop")
    return [
        f"Application: 3D Slicer {slicer.app.applicationVersion}, "
        f"revision {slicer.app.repositoryRevision}",
        f"Modules loaded: {total} "
        f"({counts['CLI']} CLI, {counts['loadable']} loadable, {counts['scripted']} scripted)",
        "This is stock Slicer. The branded Corporea shell and our modules are not in it yet.",
    ]


def act_load() -> list[str]:
    """platform: load one public scan and show it in the standard four-up layout."""
    _reset_scene()
    started = time.perf_counter()
    node = _load("MR-head.nrrd", "MRHead (public sample)")
    elapsed = time.perf_counter() - started
    _layout(LAYOUT.SlicerLayoutFourUpView)
    slicer.app.processEvents()
    _show_in_slices(node, ("Red", "Yellow", "Green"))
    for name in ("Red", "Yellow", "Green"):
        slicer.app.layoutManager().sliceWidget(name).mrmlSliceNode().SetSliceVisible(True)
    _orientation_marker(("Red", "Yellow", "Green"))
    _reset_camera()
    slicer.util.selectModule("Volumes")
    _caption("Platform: slice views of a public sample scan")
    return [
        "Scan: MRHead, a public 3D Slicer sample donated for unrestricted use",
        f"Geometry: {_geometry(node)}",
        f"Read from local disk in {elapsed:.2f} s, no network involved",
    ]


def act_render3d() -> list[str]:
    """platform: GPU volume rendering of the same scan, with an informal frame time."""
    _reset_scene()
    node = _load("MR-head.nrrd", "MRHead (public sample)")
    _show_in_slices(node, ("Red", "Yellow", "Green"))
    logic = slicer.modules.volumerendering.logic()
    display = logic.CreateDefaultVolumeRenderingNodes(node)
    display.GetVolumePropertyNode().Copy(logic.GetPresetByName("MR-Default"))
    display.SetVisibility(True)
    _layout(LAYOUT.SlicerLayoutOneUp3DView)
    # Not selectModule("VolumeRendering"): opening that module's panel closes the application
    # in this build (Slicer 5.12.3 against system Qt 6 on Fedora 44). The rendering itself is
    # unaffected, so the act drives it through the logic and leaves the panel alone.
    slicer.util.selectModule("Data")
    _caption("Platform: GPU volume rendering of a public sample scan")
    slicer.app.processEvents()
    _reset_camera()
    view = slicer.app.layoutManager().threeDWidget(0).threeDView()
    view.yawDirection = view.YawLeft
    view.forceRender()
    started = time.perf_counter()
    for _ in range(RENDER_TIMING_FRAMES):
        view.yaw()
        view.forceRender()
    frame_ms = 1000.0 * (time.perf_counter() - started) / RENDER_TIMING_FRAMES
    renderer = view.renderWindow().ReportCapabilities()
    gpu = next(
        (line.split(":", 1)[1].strip() for line in renderer.splitlines() if "renderer" in line),
        "not reported",
    )
    return [
        "Renderer: VTK GPU ray casting, supplied by the platform",
        f"Graphics device: {gpu}",
        f"Frame time over {RENDER_TIMING_FRAMES} forced renders: {frame_ms:.1f} ms "
        "(informal, taken with the demo running; not a benchmark number)",
    ]


def _grow_from_seed(volume: slicer.vtkMRMLScalarVolumeNode, multiplier: float) -> np.ndarray:
    """ITK confidence-connected region growing from one seed voxel. Returns a 0/1 array."""
    import SimpleITK as sitk
    import sitkUtils

    image = sitk.Cast(sitkUtils.PullVolumeFromSlicer(volume), sitk.sitkFloat32)
    smoothed = sitk.CurvatureFlow(image, timeStep=0.125, numberOfIterations=5)
    grown = sitk.ConfidenceConnected(
        smoothed,
        seedList=[SEED_IJK],
        numberOfIterations=2,
        multiplier=multiplier,
        initialNeighborhoodRadius=2,
        replaceValue=1,
    )
    return sitk.GetArrayFromImage(grown).astype(np.uint8)


def act_segment() -> list[str]:
    """platform: ITK region growing, Segmentations and Segment Statistics, driven from Python."""
    import SegmentStatistics

    _reset_scene()
    volume = _load("RegLib_C01_1.nrrd", "MRBrainTumor1 (public sample)")
    _layout(LAYOUT.SlicerLayoutFourUpView)
    slicer.app.processEvents()
    _show_in_slices(volume, ("Red", "Yellow", "Green"))
    _orientation_marker(("Red", "Yellow", "Green"))

    started = time.perf_counter()
    masks = {multiplier: _grow_from_seed(volume, multiplier) for multiplier in SEED_MULTIPLIERS}
    elapsed = time.perf_counter() - started
    voxel_cm3 = float(np.prod(volume.GetSpacing())) / 1000.0
    sweep = ", ".join(
        f"{multiplier:.1f} gives {masks[multiplier].sum() * voxel_cm3:.1f} cm3"
        for multiplier in SEED_MULTIPLIERS
    )

    segmentation = slicer.mrmlScene.AddNewNodeByClass(
        "vtkMRMLSegmentationNode", "Region growing output (tool demo)"
    )
    segmentation.CreateDefaultDisplayNodes()
    segmentation.SetReferenceImageGeometryParameterFromVolumeNode(volume)
    segment_id = segmentation.GetSegmentation().AddEmptySegment(
        "seeded-region", "Seeded region (tool demo, not a finding)", (0.80, 0.16, 0.36)
    )
    slicer.util.updateSegmentBinaryLabelmapFromArray(
        masks[SEED_MULTIPLIER_SHOWN], segmentation, segment_id, volume
    )
    segmentation.CreateClosedSurfaceRepresentation()
    segmentation.GetDisplayNode().SetOpacity2DFill(0.35)

    stats = SegmentStatistics.SegmentStatisticsLogic()
    parameters = stats.getParameterNode()
    parameters.SetParameter("Segmentation", segmentation.GetID())
    parameters.SetParameter("ScalarVolume", volume.GetID())
    stats.computeStatistics()
    volume_cm3 = stats.getStatistics()[segment_id, "LabelmapSegmentStatisticsPlugin.volume_cm3"]

    centre = segmentation.GetSegmentCenterRAS(segment_id)
    slicer.modules.markups.logic().JumpSlicesToLocation(centre[0], centre[1], centre[2], True)
    _reset_camera()
    slicer.util.selectModule("SegmentEditor")
    _caption("Platform: region growing from one seed, run from a Python script")
    return [
        "Scan: MRBrainTumor1, a public 3D Slicer sample. Not a patient of ours.",
        "Method: ITK confidence-connected region growing from one seed voxel, then Slicer's "
        "Segment Statistics. All of it is supplied by the platform.",
        f"Shown: multiplier {SEED_MULTIPLIER_SHOWN:.1f}, one segment, {volume_cm3:.1f} cm3. "
        f"Three runs took {elapsed:.1f} s.",
        f"Same seed, three settings: {sweep}.",
        "One parameter moves the volume this much. That is why no volume is reported as a "
        "result until it has been scored against ground truth (Dice, HD95, ASSD).",
        "Tool demonstration only: not our segmenter, not validated, not a clinical finding.",
    ]


def act_compare() -> list[str]:
    """platform: two scans side by side. The record and the timeline are what we add."""
    _reset_scene()
    first = _load("RegLib_C01_1.nrrd", "MRBrainTumor1 (public sample)")
    second = _load("RegLib_C01_2.nrrd", "MRBrainTumor2 (public sample)")
    matrix = vtk.vtkMatrix4x4()
    first.GetIJKToRASMatrix(matrix)
    seed_ras = matrix.MultiplyPoint([*SEED_IJK, 1.0])[:3]
    _layout(LAYOUT.SlicerLayoutSideBySideView)
    slicer.app.processEvents()
    manager = slicer.app.layoutManager()
    for name, node in (("Red", first), ("Yellow", second)):
        widget = manager.sliceWidget(name)
        widget.mrmlSliceNode().SetOrientationToAxial()
        composite = widget.sliceLogic().GetSliceCompositeNode()
        composite.SetBackgroundVolumeID(node.GetID())
        composite.SetLinkedControl(True)
        widget.sliceLogic().FitSliceToAll()
        # The same world position in both views. Nothing has been registered, so the two
        # views are not guaranteed to show the same anatomy, which is the point of the step.
        widget.mrmlSliceNode().JumpSliceByOffsetting(*seed_ras)
    _orientation_marker(("Red", "Yellow"))
    slicer.util.selectModule("Data")
    _caption("Platform: two scans side by side, same world position, not registered")
    return [
        "Scans: MRBrainTumor1 and MRBrainTumor2, the public pair Slicer's own registration "
        "example aligns. Used here as a stand-in for two visits.",
        f"Left view:  {_geometry(first)}",
        f"Right view: {_geometry(second)}",
        f"Both views sit at the same world position, S = {seed_ras[2]:.1f} mm, and the grids "
        "differ, so nothing can be compared until the scans are registered. "
        "Registration is supplied by the platform. The longitudinal record is ours to build.",
    ]


def _marker_centre_mm(node: slicer.vtkMRMLScalarVolumeNode, label: int) -> np.ndarray:
    """World-space centre of one phantom marker, computed from the voxels and the affine."""
    kji = np.argwhere(slicer.util.arrayFromVolume(node) == label).mean(axis=0)
    matrix = vtk.vtkMatrix4x4()
    node.GetIJKToRASMatrix(matrix)
    ras = matrix.MultiplyPoint([kji[2], kji[1], kji[0], 1.0])
    return np.array(ras[:3])


def act_phantom() -> list[str]:
    """ours: the orientation phantom, correct and deliberately flipped, side by side."""
    _reset_scene()
    good = slicer.util.loadVolume(
        os.path.join(ROOT, "build", "phantom.nii.gz"),
        {"name": "Phantom, correct", "show": False},
    )
    broken = slicer.util.loadVolume(
        os.path.join(ROOT, "build", "phantom-broken-lr.nii.gz"),
        {"name": "Phantom, flipped left to right", "show": False},
    )
    _layout(LAYOUT.SlicerLayoutSideBySideView)
    slicer.app.processEvents()
    manager = slicer.app.layoutManager()
    for name, node in (("Red", good), ("Yellow", broken)):
        widget = manager.sliceWidget(name)
        widget.mrmlSliceNode().SetOrientationToAxial()
        widget.sliceLogic().GetSliceCompositeNode().SetBackgroundVolumeID(node.GetID())
        widget.sliceLogic().FitSliceToAll()
        # Move to the marker's slice without recentring, so both views keep the whole phantom
        # in frame and the marker is seen to change sides.
        slice_node = widget.mrmlSliceNode()
        slice_node.JumpSliceByOffsetting(*PHANTOM_LEFT_MARKER_MM)
        field_of_view = slice_node.GetFieldOfView()
        slice_node.SetFieldOfView(
            field_of_view[0] * PHANTOM_ZOOM_OUT,
            field_of_view[1] * PHANTOM_ZOOM_OUT,
            field_of_view[2],
        )
    _orientation_marker(("Red", "Yellow"))
    slicer.util.selectModule("Data")
    _caption("Ours: the orientation phantom")
    good_centre = _marker_centre_mm(good, PHANTOM_LEFT_MARKER_LABEL)
    broken_centre = _marker_centre_mm(broken, PHANTOM_LEFT_MARKER_LABEL)

    def side(x_mm: float) -> str:
        return "patient left" if x_mm < 0 else "patient right"

    return [
        "Two synthetic volumes from scripts/make_phantom.py. No patient data.",
        f"Left view, correct:  marker centre x = {good_centre[0]:+.1f} mm, {side(good_centre[0])}",
        f"Right view, flipped: marker centre x = {broken_centre[0]:+.1f} mm, "
        f"{side(broken_centre[0])}",
        "Both files carry the same header and both look like valid scans. Only the marker "
        "tells them apart, which is why the check is automated and runs on every commit.",
    ]


def _mock_regions() -> dict[str, tuple[slice, slice, slice]]:
    """Six boxes with made-up names. A stand-in for a parcellation, deliberately not anatomy."""
    return {
        "MOCK region A": (slice(20, 48), slice(20, 48), slice(20, 48)),
        "MOCK region B": (slice(48, 76), slice(20, 48), slice(20, 48)),
        "MOCK region C": (slice(20, 48), slice(48, 76), slice(20, 48)),
        "MOCK region D": (slice(48, 76), slice(48, 76), slice(20, 48)),
        "MOCK region E": (slice(20, 48), slice(20, 76), slice(48, 76)),
        "MOCK region F": (slice(48, 76), slice(20, 76), slice(48, 76)),
    }


def act_mock_attribution() -> list[str]:
    """mock: the shape of the R2 result. Mask intersected with regions, ranked, nothing hidden."""
    _reset_scene()
    grid = np.indices(MOCK_SHAPE)
    distance = np.sqrt(sum((grid[i] - MOCK_LESION_CENTRE[i]) ** 2 for i in range(3)))
    lesion = distance <= MOCK_LESION_RADIUS

    segmentation = slicer.mrmlScene.AddNewNodeByClass(
        "vtkMRMLSegmentationNode", "MOCK scene, synthetic, not anatomy"
    )
    segmentation.CreateDefaultDisplayNodes()
    reference = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", "mock-grid")
    slicer.util.updateVolumeFromArray(reference, np.zeros(MOCK_SHAPE, dtype=np.uint8))
    segmentation.SetReferenceImageGeometryParameterFromVolumeNode(reference)

    def add_segment(name: str, mask: np.ndarray, colour: tuple[float, float, float]) -> str:
        segment_id = segmentation.GetSegmentation().AddEmptySegment(name, name, colour)
        slicer.util.updateSegmentBinaryLabelmapFromArray(
            mask.astype(np.uint8), segmentation, segment_id, reference
        )
        return segment_id

    palette = [
        (0.36, 0.52, 0.70),
        (0.45, 0.62, 0.55),
        (0.62, 0.58, 0.40),
        (0.52, 0.48, 0.68),
        (0.40, 0.62, 0.68),
        (0.60, 0.52, 0.52),
    ]
    rows = []
    display = segmentation.GetDisplayNode()
    for (name, box), colour in zip(_mock_regions().items(), palette, strict=True):
        mask = np.zeros(MOCK_SHAPE, dtype=bool)
        mask[box] = True
        segment_id = add_segment(name, mask, colour)
        display.SetSegmentOpacity3D(segment_id, 0.25)
        overlap = int(np.count_nonzero(mask & lesion))
        rows.append((name, overlap, int(mask.sum())))
    lesion_id = add_segment("MOCK lesion mask", lesion, (0.80, 0.16, 0.36))
    display.SetSegmentOpacity3D(lesion_id, 1.0)
    segmentation.CreateClosedSurfaceRepresentation()

    lesion_voxels = int(lesion.sum())
    rows.sort(key=lambda row: row[1], reverse=True)
    table = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLTableNode", "MOCK attribution table")
    columns = ["Rank", "Region (made-up names)", "Overlap mm3", "% of lesion", "% of region"]
    for title in columns:
        table.AddColumn().SetName(title)
    for rank, (name, overlap, region_voxels) in enumerate(rows, start=1):
        row = table.AddEmptyRow()
        values = [
            str(rank),
            name,
            str(overlap),
            f"{100.0 * overlap / lesion_voxels:.1f}",
            f"{100.0 * overlap / region_voxels:.1f}",
        ]
        for column, value in enumerate(values):
            table.SetCellText(row, column, value)
    table.SetLocked(True)

    _layout(LAYOUT.SlicerLayout3DTableView)
    slicer.app.applicationLogic().GetSelectionNode().SetActiveTableID(table.GetID())
    slicer.app.applicationLogic().PropagateTableSelection()
    slicer.app.processEvents()
    _reset_camera()
    slicer.util.selectModule("Tables")
    _caption("MOCK: synthetic lesion and made-up regions. Not anatomy.")
    outside = lesion_voxels - sum(row[1] for row in rows)
    lines = [
        "Synthetic scene: one sphere as a lesion mask, six boxes as regions. Grid is 1 mm, "
        "so voxels are mm3.",
        f"Lesion mask: {lesion_voxels} mm3, of which {outside} mm3 falls outside every region",
    ]
    for rank, (name, overlap, _region_voxels) in enumerate(rows, start=1):
        lines.append(
            f"  {rank}. {name}: {overlap} mm3, {100.0 * overlap / lesion_voxels:.1f}% of the lesion"
        )
    lines.append(
        "Every region is listed, including the ones with zero overlap. Rank, never suppress."
    )
    lines.append(
        "The real engine needs a real atlas and a registered scan. Neither exists yet (ADR-006)."
    )
    return lines


def act_quit() -> list[str]:
    qt.QTimer.singleShot(300, lambda: slicer.app.exit(0))
    return ["Slicer is closing."]


ACTS: dict[str, Callable[[], list[str]]] = {
    "platform": act_platform,
    "load": act_load,
    "render3d": act_render3d,
    "segment": act_segment,
    "compare": act_compare,
    "phantom": act_phantom,
    "mock_attribution": act_mock_attribution,
    "quit": act_quit,
}


def _write_status(sequence: str, outcome: str, lines: list[str]) -> None:
    """Write then rename, so the terminal never reads a half-written file."""
    temporary = os.path.join(STATE, "status.tmp")
    with open(temporary, "w", encoding="utf-8") as handle:
        handle.write("\n".join([f"{sequence} {outcome}", *lines]) + "\n")
    os.replace(temporary, os.path.join(STATE, "status"))


def _screenshot(name: str) -> None:
    slicer.app.processEvents()
    slicer.util.forceRenderAllViews()
    slicer.app.processEvents()
    slicer.util.mainWindow().grab().save(os.path.join(SHOTS, f"{name}.png"))


class Driver:
    """Polls the control file and runs one act per new sequence number."""

    def __init__(self) -> None:
        self.last_sequence = ""
        self.timer = qt.QTimer()
        self.timer.setInterval(POLL_INTERVAL_MS)
        self.timer.connect("timeout()", self.poll)
        self.timer.start()

    def poll(self) -> None:
        try:
            with open(os.path.join(STATE, "control"), encoding="utf-8") as handle:
                sequence, name = handle.read().split()
        except (FileNotFoundError, ValueError):
            return
        if sequence == self.last_sequence:
            return
        self.last_sequence = sequence
        act = ACTS.get(name)
        if act is None:
            _write_status(sequence, "error", [f"Unknown act: {name}"])
            return
        try:
            lines = act()
            if SHOTS and name != "quit":
                _screenshot(name)
        except Exception as error:  # noqa: BLE001 - reported to the presenter, never swallowed
            traceback.print_exc()
            _write_status(sequence, "error", [f"{type(error).__name__}: {error}"])
            return
        _write_status(sequence, "ok", lines)


def _start() -> None:
    main_window = slicer.util.mainWindow()
    main_window.showMaximized()
    slicer.util.setPythonConsoleVisible(False)
    slicer.modules.corporeaDemoDriver = Driver()
    with open(os.path.join(STATE, "ready"), "w", encoding="utf-8") as handle:
        handle.write("ready\n")


_start()
