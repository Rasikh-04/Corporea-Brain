"""Organ manifest validation, per ``docs/04-ORGAN_MODULE_SPEC.md``.

The manifest is what turns "we built an organ-agnostic platform and implemented the brain to
depth in it" from a claim into a structural property: the application reads implementation
level from data and shows it, so a stub organ says "stub" in its own header and nobody can
allege over-claiming.

Two rules from ``docs/04`` shape everything here.

**A manifest that fails validation is reported with the specific failing field, and the organ
is excluded. It is never silently skipped.** So validation collects every issue rather than
raising on the first, and each issue carries a dotted field path. Hence a hand-written checker
rather than ``jsonschema``: "geometry.layers[1].mesh is missing" sends someone to a line,
"document does not conform" sends them to the whole file.

**Checks that cannot run yet are reported as deferred, never omitted.** Three of the seven in
``docs/04`` are blocked: asset existence and checksums have no committed assets to check,
disorder ids have no catalog to resolve against, and parcellation ids wait on ADR-006. A check
that quietly does not run is worse than one that fails, because it leaves a green result
standing for something nobody verified.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Any, Final

import yaml

__all__ = [
    "Level",
    "Severity",
    "Issue",
    "ManifestReport",
    "SCHEMA_VERSION",
    "APPROVED_LICENCES",
    "validate_manifest",
    "validate_file",
    "validate_directory",
]

SCHEMA_VERSION: Final[int] = 1

# docs/13-LEGAL_AND_ETHICS.md, asset licence register. An organ whose geometry carries
# anything else does not ship until that entry exists, because the audit happens before
# release and a missing entry found then is a release blocker.
APPROVED_LICENCES: Final[frozenset[str]] = frozenset(
    {"CC BY-SA 4.0", "CC BY-SA 2.1 JP", "CC BY 4.0", "Apache-2.0", "MIT"}
)

# docs/04, implementation levels table. A capability the level does not support is not a
# harmless extra field: capabilities drive which UI affordances render, so declaring
# `attribution` on a stub would put patient-specific quantification in front of a mesh that
# cannot support it.
CAPABILITIES_BY_LEVEL: Final[dict[str, frozenset[str]]] = {
    "stub": frozenset(),
    "shallow": frozenset({"navigation"}),
    "deep": frozenset({"segmentation", "attribution", "deficits", "navigation", "longitudinal"}),
}

REQUIRED_CAPABILITIES_BY_LEVEL: Final[dict[str, frozenset[str]]] = {
    "stub": frozenset(),
    "shallow": frozenset(),
    "deep": frozenset({"segmentation", "attribution", "deficits", "longitudinal"}),
}


# StrEnum, not `(str, Enum)`, and the difference is worth stating because it is the kind of
# thing that changes output without changing behaviour anywhere a test looks. Under StrEnum,
# `str(Level.STUB)` and `f"{Level.STUB}"` are `"stub"`; under `(str, Enum)` they are
# `"Level.STUB"`. Manifest field values are what these mean, so the StrEnum reading is the
# one that is right when a level or a severity reaches a message or a report.
class Level(StrEnum):
    STUB = "stub"
    SHALLOW = "shallow"
    DEEP = "deep"


class Severity(StrEnum):
    """``ERROR`` excludes the organ. ``DEFERRED`` is a check that could not run.

    There is no ``WARNING``. A manifest is either loadable or it is not, and a middle category
    is where things go to be ignored.
    """

    ERROR = "error"
    DEFERRED = "deferred"


@dataclass(frozen=True)
class Issue:
    field: str
    message: str
    severity: Severity = Severity.ERROR

    def __str__(self) -> str:
        return f"[{self.severity.value}] {self.field}: {self.message}"


@dataclass(frozen=True)
class ManifestReport:
    """Everything found in one manifest. Valid means no errors; deferred checks do not block."""

    path: Path
    organ: str | None
    issues: tuple[Issue, ...] = field(default=())

    @property
    def errors(self) -> tuple[Issue, ...]:
        return tuple(i for i in self.issues if i.severity is Severity.ERROR)

    @property
    def deferred(self) -> tuple[Issue, ...]:
        return tuple(i for i in self.issues if i.severity is Severity.DEFERRED)

    @property
    def is_valid(self) -> bool:
        return not self.errors

    def describe(self) -> str:
        verdict = "valid" if self.is_valid else f"INVALID, {len(self.errors)} error(s)"
        lines = [f"{self.path}: organ {self.organ or '<unnamed>'} is {verdict}"]
        lines.extend(f"  {issue}" for issue in self.issues)
        return "\n".join(lines)


def validate_file(path: Path) -> ManifestReport:
    """Read and validate one manifest. Unreadable or malformed YAML is an error, not a crash."""
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    except OSError as exc:
        return ManifestReport(path, None, (Issue("<file>", f"cannot read: {exc}"),))
    except yaml.YAMLError as exc:
        return ManifestReport(path, None, (Issue("<file>", f"is not valid YAML: {exc}"),))

    if not isinstance(raw, dict):
        return ManifestReport(
            path, None, (Issue("<document>", f"must be a mapping, got {type(raw).__name__}"),)
        )
    return ManifestReport(path, raw.get("organ"), tuple(validate_manifest(raw)))


def validate_directory(root: Path) -> tuple[ManifestReport, ...]:
    """Validate every ``*/manifest.yaml`` under ``root``, in a stable order."""
    return tuple(validate_file(p) for p in sorted(root.glob("*/manifest.yaml")))


def validate_manifest(manifest: dict[str, Any]) -> list[Issue]:
    """Every issue in one parsed manifest. Collects, never raises, never stops at the first."""
    issues: list[Issue] = []
    issues.extend(_check_identity(manifest))
    level = manifest.get("implementation_level")
    issues.extend(_check_geometry(manifest, level))
    issues.extend(_check_capabilities(manifest, level))
    issues.extend(_check_provenance(manifest))
    issues.extend(_check_level_dependent_lists(manifest, level))
    issues.extend(_deferred_checks(manifest))
    return issues


def _check_identity(manifest: dict[str, Any]) -> list[Issue]:
    issues: list[Issue] = []
    organ = manifest.get("organ")
    if not isinstance(organ, str) or not organ:
        issues.append(Issue("organ", "is required and must be a non-empty string"))
    elif organ != organ.lower() or " " in organ or "_" in organ:
        issues.append(
            Issue("organ", f"{organ!r} must be a lowercase hyphenated slug, per docs/14 naming")
        )

    if not isinstance(manifest.get("display_name"), str) or not manifest.get("display_name"):
        issues.append(Issue("display_name", "is required and must be a non-empty string"))

    level = manifest.get("implementation_level")
    if level not in {member.value for member in Level}:
        issues.append(
            Issue(
                "implementation_level",
                f"{level!r} is not one of stub, shallow, deep. It drives the UI badge and "
                f"capability gating, so there is no sensible default.",
            )
        )

    version = manifest.get("schema_version")
    if version != SCHEMA_VERSION:
        issues.append(Issue("schema_version", f"expected {SCHEMA_VERSION}, got {version!r}"))
    return issues


def _check_geometry(manifest: dict[str, Any], level: Any) -> list[Issue]:
    geometry = manifest.get("geometry")
    if not isinstance(geometry, dict):
        return [Issue("geometry", "is required at every implementation level")]

    issues: list[Issue] = []
    if not isinstance(geometry.get("entry_mesh"), str) or not geometry.get("entry_mesh"):
        issues.append(
            Issue("geometry.entry_mesh", "is required: it is what renders when the organ is picked")
        )

    layers = geometry.get("layers")
    if layers is None:
        if level in {Level.DEEP.value, Level.SHALLOW.value}:
            issues.append(Issue("geometry.layers", f"is required for implementation_level {level}"))
        return issues

    if not isinstance(layers, list):
        return issues + [Issue("geometry.layers", "must be a list")]

    seen: set[str] = set()
    for index, layer in enumerate(layers):
        prefix = f"geometry.layers[{index}]"
        if not isinstance(layer, dict):
            issues.append(Issue(prefix, "must be a mapping with id and mesh"))
            continue
        layer_id = layer.get("id")
        if not isinstance(layer_id, str) or not layer_id:
            issues.append(Issue(f"{prefix}.id", "is required"))
        elif layer_id in seen:
            issues.append(
                Issue(f"{prefix}.id", f"{layer_id!r} is a duplicate; layers toggle by id")
            )
        else:
            seen.add(layer_id)
        if not isinstance(layer.get("mesh"), str) or not layer.get("mesh"):
            issues.append(Issue(f"{prefix}.mesh", "is required"))
    return issues


def _check_capabilities(manifest: dict[str, Any], level: Any) -> list[Issue]:
    capabilities = manifest.get("capabilities")
    if capabilities is None:
        return [
            Issue(
                "capabilities",
                "is required at every level. An absent list is not the same as an empty one: "
                "empty is a claim that this organ offers no analysis, and stubs must make it.",
            )
        ]
    if not isinstance(capabilities, list):
        return [Issue("capabilities", "must be a list")]
    if level not in CAPABILITIES_BY_LEVEL:
        return []

    issues: list[Issue] = []
    allowed = CAPABILITIES_BY_LEVEL[level]
    for capability in capabilities:
        if capability not in allowed:
            issues.append(
                Issue(
                    "capabilities",
                    f"{capability!r} is not available at implementation_level {level}. "
                    f"Capabilities render UI affordances, so declaring one the level cannot "
                    f"support puts an empty analysis panel in front of a clinician.",
                )
            )
    missing = REQUIRED_CAPABILITIES_BY_LEVEL[level] - set(capabilities)
    if missing:
        issues.append(
            Issue(
                "capabilities",
                f"implementation_level {level} must declare {sorted(missing)}",
            )
        )
    return issues


def _check_provenance(manifest: dict[str, Any]) -> list[Issue]:
    provenance = manifest.get("provenance")
    if not isinstance(provenance, dict):
        return [Issue("provenance", "is required at every level, including stub")]

    issues: list[Issue] = []
    for key in ("source", "generated_by"):
        if not isinstance(provenance.get(key), str) or not provenance.get(key):
            issues.append(Issue(f"provenance.{key}", "is required"))

    licence = provenance.get("licence")
    if not isinstance(licence, str) or not licence:
        issues.append(Issue("provenance.licence", "is required and is audited before release"))
    elif licence not in APPROVED_LICENCES:
        issues.append(
            Issue(
                "provenance.licence",
                f"{licence!r} is not in the licence register in docs/13. Add the register "
                f"entry first: a missing entry found during the pre-release audit blocks the "
                f"release.",
            )
        )

    issues.extend(_check_known_gaps(provenance))
    return issues


def _check_known_gaps(provenance: dict[str, Any]) -> list[Issue]:
    """``known_gaps`` is the field most likely to be treated as optional. It is not.

    Present on every manifest including stubs, because an empty list is a claim that the
    geometry is complete and that claim needs evidence.
    """
    gaps = provenance.get("known_gaps")
    if gaps is None:
        return [
            Issue(
                "provenance.known_gaps",
                "is required and may be empty, but must be present. An absent list is "
                "indistinguishable from a complete inventory that found nothing, and the "
                "difference is the whole point of the field.",
            )
        ]
    if not isinstance(gaps, list):
        return [Issue("provenance.known_gaps", "must be a list")]

    issues: list[Issue] = []
    for index, gap in enumerate(gaps):
        prefix = f"provenance.known_gaps[{index}]"
        if not isinstance(gap, dict):
            issues.append(Issue(prefix, "must be a mapping"))
            continue
        for key in ("id", "statement", "consequence"):
            if not isinstance(gap.get(key), str) or not gap.get(key):
                issues.append(
                    Issue(
                        f"{prefix}.{key}",
                        "is required. A gap without a consequence is a note; docs/04 needs a "
                        "constraint the UI and the report both honour.",
                    )
                )
        if "affects_layers" not in gap:
            issues.append(
                Issue(
                    f"{prefix}.affects_layers",
                    "is required and may be empty. The UI surfaces a gap on the layer it "
                    "affects, at the point of use, not in an About dialog.",
                )
            )
        elif not isinstance(gap.get("affects_layers"), list):
            issues.append(Issue(f"{prefix}.affects_layers", "must be a list"))
    return issues


def _check_level_dependent_lists(manifest: dict[str, Any], level: Any) -> list[Issue]:
    issues: list[Issue] = []
    for key in ("supported_modalities", "disorders", "parcellations"):
        value = manifest.get(key)
        if value is not None and not isinstance(value, list):
            issues.append(Issue(key, "must be a list"))

    if level in {Level.DEEP.value, Level.SHALLOW.value} and not manifest.get("disorders"):
        issues.append(Issue("disorders", f"is required and non-empty for level {level}"))
    if level == Level.DEEP.value and not manifest.get("parcellations"):
        issues.append(Issue("parcellations", "is required for level deep; the first is default"))
    if level == Level.STUB.value and manifest.get("parcellations"):
        issues.append(
            Issue(
                "parcellations",
                "must be absent for a stub, which claims nothing below the surface",
            )
        )
    return issues


def _deferred_checks(manifest: dict[str, Any]) -> list[Issue]:
    """The three checks in ``docs/04`` that cannot run yet. Reported, never omitted."""
    issues = [
        Issue(
            "geometry.*",
            "asset existence and checksum not checked: no assets are committed, and by "
            "docs/13 they are fetched rather than redistributed. Wire this when the export "
            "pipeline lands.",
            Severity.DEFERRED,
        ),
        Issue(
            "provenance.known_gaps",
            "not verified against the geometry. docs/04 requires gaps be discovered by "
            "inventorying meshes, never by reading the source's description files. Nothing "
            "here can confirm that happened.",
            Severity.DEFERRED,
        ),
    ]
    if manifest.get("disorders"):
        issues.append(
            Issue(
                "disorders",
                "ids not resolved: the disorder catalog does not exist yet.",
                Severity.DEFERRED,
            )
        )
    if manifest.get("parcellations"):
        issues.append(
            Issue(
                "parcellations",
                "ids not resolved: ADR-006 is open, so there is no coordinate space or atlas "
                "to resolve them against. Seam 5 forbids picking one here.",
                Severity.DEFERRED,
            )
        )
    return issues
