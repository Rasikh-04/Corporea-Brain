"""Organ manifest validation, per ``docs/04-ORGAN_MODULE_SPEC.md``.

The behaviour that matters most is the one in the spec's own words: a manifest that fails
validation is reported with the specific failing field, and the organ is excluded. It is never
silently skipped. So most of these tests check that a broken manifest produces a *named* issue,
not merely that it fails.
"""

from __future__ import annotations

import copy
from pathlib import Path

import pytest
from corporea_core.organ_manifest import (
    Severity,
    validate_directory,
    validate_file,
    validate_manifest,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
ORGANS = REPO_ROOT / "organs"


def fields_of(issues, severity=Severity.ERROR) -> set[str]:
    return {issue.field for issue in issues if issue.severity is severity}


@pytest.fixture
def valid_stub() -> dict:
    return {
        "organ": "heart",
        "display_name": "Heart",
        "implementation_level": "stub",
        "schema_version": 1,
        "geometry": {"entry_mesh": "assets/heart/shell.glb"},
        "supported_modalities": [],
        "disorders": [],
        "capabilities": [],
        "provenance": {
            "source": "BodyParts3D",
            "licence": "CC BY-SA 2.1 JP",
            "generated_by": "pipeline/atlas/export_stub.py@v0.1.0",
            "known_gaps": [
                {
                    "id": "shell-only",
                    "statement": "External surface only. No chambers, valves or vessels.",
                    "affects_layers": [],
                    "consequence": "Identification only. No anatomical claim below the surface.",
                }
            ],
        },
    }


class TestTheCommittedManifests:
    def test_the_registry_is_not_empty(self) -> None:
        assert validate_directory(ORGANS), "no organ manifests found; check the glob"

    def test_every_committed_manifest_is_valid(self) -> None:
        for report in validate_directory(ORGANS):
            assert report.is_valid, report.describe()

    def test_the_brain_manifest_declares_its_deep_capabilities(self) -> None:
        report = validate_file(ORGANS / "brain" / "manifest.yaml")
        assert report.organ == "brain"
        assert report.is_valid, report.describe()

    def test_deferred_checks_are_reported_rather_than_omitted(self) -> None:
        # docs/04 lists seven checks. Three cannot run yet. A green result that quietly stood
        # for an unverified check is worse than a red one.
        report = validate_file(ORGANS / "brain" / "manifest.yaml")
        assert report.deferred
        assert any("ADR-006" in issue.message for issue in report.deferred)


class TestRequiredFields:
    def test_a_valid_stub_produces_no_errors(self, valid_stub) -> None:
        assert not fields_of(validate_manifest(valid_stub))

    @pytest.mark.parametrize(
        "missing", ["organ", "display_name", "implementation_level", "schema_version", "geometry"]
    )
    def test_each_required_field_is_named_when_absent(self, valid_stub, missing) -> None:
        manifest = copy.deepcopy(valid_stub)
        del manifest[missing]
        assert missing in fields_of(validate_manifest(manifest))

    def test_an_unknown_implementation_level_is_rejected(self, valid_stub) -> None:
        manifest = {**valid_stub, "implementation_level": "medium"}
        assert "implementation_level" in fields_of(validate_manifest(manifest))

    def test_an_organ_id_must_be_a_lowercase_slug(self, valid_stub) -> None:
        manifest = {**valid_stub, "organ": "Left_Heart"}
        assert "organ" in fields_of(validate_manifest(manifest))

    def test_a_wrong_schema_version_is_rejected(self, valid_stub) -> None:
        manifest = {**valid_stub, "schema_version": 2}
        assert "schema_version" in fields_of(validate_manifest(manifest))


class TestKnownGapsIsLoadBearing:
    def test_an_absent_known_gaps_list_is_an_error(self, valid_stub) -> None:
        manifest = copy.deepcopy(valid_stub)
        del manifest["provenance"]["known_gaps"]
        assert "provenance.known_gaps" in fields_of(validate_manifest(manifest))

    def test_an_empty_known_gaps_list_is_allowed(self, valid_stub) -> None:
        # Allowed, because it is a claim someone may be entitled to make. Required to be
        # present, because an absent list makes no claim at all and looks identical.
        manifest = copy.deepcopy(valid_stub)
        manifest["provenance"]["known_gaps"] = []
        assert not fields_of(validate_manifest(manifest))

    @pytest.mark.parametrize("missing", ["id", "statement", "consequence"])
    def test_a_gap_without_a_consequence_is_only_a_note(self, valid_stub, missing) -> None:
        manifest = copy.deepcopy(valid_stub)
        del manifest["provenance"]["known_gaps"][0][missing]
        assert f"provenance.known_gaps[0].{missing}" in fields_of(validate_manifest(manifest))

    def test_affects_layers_must_be_present_even_when_empty(self, valid_stub) -> None:
        manifest = copy.deepcopy(valid_stub)
        del manifest["provenance"]["known_gaps"][0]["affects_layers"]
        assert "provenance.known_gaps[0].affects_layers" in fields_of(validate_manifest(manifest))


class TestCapabilitiesAreGatedByLevel:
    def test_a_stub_may_not_claim_attribution(self, valid_stub) -> None:
        # Capabilities render UI affordances. A stub claiming attribution puts a
        # patient-specific analysis panel in front of a mesh that cannot support one.
        manifest = {**valid_stub, "capabilities": ["attribution"]}
        assert "capabilities" in fields_of(validate_manifest(manifest))

    def test_a_deep_organ_must_declare_its_analysis_capabilities(self, valid_stub) -> None:
        manifest = {
            **valid_stub,
            "implementation_level": "deep",
            "capabilities": ["navigation"],
            "disorders": ["glioma"],
            "parcellations": ["<PARCELLATION>"],
            "geometry": {
                "entry_mesh": "a.glb",
                "layers": [{"id": "cortex", "mesh": "cortex.glb"}],
            },
        }
        assert "capabilities" in fields_of(validate_manifest(manifest))

    def test_an_absent_capabilities_list_is_not_the_same_as_an_empty_one(self, valid_stub) -> None:
        manifest = copy.deepcopy(valid_stub)
        del manifest["capabilities"]
        assert "capabilities" in fields_of(validate_manifest(manifest))


class TestGeometryAndLicence:
    def test_duplicate_layer_ids_are_rejected(self, valid_stub) -> None:
        manifest = {
            **valid_stub,
            "implementation_level": "shallow",
            "disorders": ["otitis_media_effusion"],
            "geometry": {
                "entry_mesh": "a.glb",
                "layers": [
                    {"id": "outer", "mesh": "outer.glb"},
                    {"id": "outer", "mesh": "other.glb"},
                ],
            },
        }
        assert "geometry.layers[1].id" in fields_of(validate_manifest(manifest))

    def test_a_layer_is_named_by_index_when_it_is_incomplete(self, valid_stub) -> None:
        manifest = {
            **valid_stub,
            "implementation_level": "shallow",
            "disorders": ["otitis_media_effusion"],
            "geometry": {
                "entry_mesh": "a.glb",
                "layers": [{"id": "outer", "mesh": "outer.glb"}, {"id": "middle"}],
            },
        }
        assert "geometry.layers[1].mesh" in fields_of(validate_manifest(manifest))

    def test_an_unregistered_licence_is_rejected(self, valid_stub) -> None:
        manifest = copy.deepcopy(valid_stub)
        manifest["provenance"]["licence"] = "Proprietary"
        issues = validate_manifest(manifest)
        assert "provenance.licence" in fields_of(issues)
        assert any("docs/13" in issue.message for issue in issues)

    def test_a_stub_may_not_declare_parcellations(self, valid_stub) -> None:
        manifest = {**valid_stub, "parcellations": ["<PARCELLATION>"]}
        assert "parcellations" in fields_of(validate_manifest(manifest))


class TestMalformedFiles:
    def test_unparseable_yaml_is_reported_and_does_not_raise(self, tmp_path) -> None:
        path = tmp_path / "manifest.yaml"
        path.write_text("organ: [unclosed\n", encoding="utf-8")
        report = validate_file(path)
        assert not report.is_valid
        assert "not valid YAML" in report.errors[0].message

    def test_a_missing_file_is_reported_and_does_not_raise(self, tmp_path) -> None:
        report = validate_file(tmp_path / "absent.yaml")
        assert not report.is_valid
        assert "cannot read" in report.errors[0].message

    def test_a_document_that_is_not_a_mapping_is_reported(self, tmp_path) -> None:
        path = tmp_path / "manifest.yaml"
        path.write_text("- brain\n- ear\n", encoding="utf-8")
        report = validate_file(path)
        assert not report.is_valid
        assert "must be a mapping" in report.errors[0].message

    def test_every_issue_in_a_broken_manifest_is_collected(self, tmp_path) -> None:
        # Reported, not stopped at the first. Fixing a manifest one error per CI run is how a
        # merge takes an afternoon.
        path = tmp_path / "manifest.yaml"
        path.write_text("organ: Brain\nschema_version: 9\n", encoding="utf-8")
        report = validate_file(path)
        assert len(report.errors) >= 4
