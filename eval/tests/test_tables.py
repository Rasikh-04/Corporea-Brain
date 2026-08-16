"""The results-table writers, and the assertion that they still match ``docs/10``.

``test_every_table_matches_the_protocol_document`` is the one that earns its keep. Everything
else here checks that the renderer behaves; that one checks that the renderer is rendering the
*right* table, by reading the specification document and comparing. It is the mechanical form
of "do not redesign them late".
"""

from __future__ import annotations

from pathlib import Path

import pytest
from corporea_eval.tables import (
    ALL_TABLES,
    PENDING,
    TABLE_4_1,
    TABLE_4_2,
    TABLE_4_4,
    TableError,
    TableSpec,
    VersionStamp,
    parse_declared_tables,
    render_table,
    write_all,
    write_table,
)

PROTOCOL = Path(__file__).resolve().parents[2] / "docs" / "10-EVALUATION_PROTOCOL.md"

STAMP = VersionStamp(
    model_version="seg-0.1.0",
    pipeline_version="0.1.0",
    dataset_version="ATLAS-v2.0",
    split_id="test-fold-0",
)


# --- The anti-drift assertion --------------------------------------------------------------


@pytest.mark.parametrize("spec", ALL_TABLES, ids=lambda spec: spec.number)
def test_every_table_matches_the_protocol_document(spec: TableSpec) -> None:
    """Columns and row labels here must be identical to the ones in ``docs/10``.

    Hand-transcribing numbers into a document is how numbers drift, and hand-transcribing a
    *table layout* out of one is how the generated table and the thesis chapter stop being the
    same table without anybody noticing. This closes that loop in the only direction that
    matters: the document is the specification, the code is checked against it.
    """
    declared = parse_declared_tables(PROTOCOL.read_text(encoding="utf-8"))

    assert spec.number in declared, (
        f"docs/10 declares no table {spec.number}. Either the document lost it or this spec "
        f"invented it."
    )
    columns, body = declared[spec.number]
    assert columns == spec.columns
    assert [row[: spec.key_columns] for row in body] == list(spec.rows)


def test_the_parser_finds_all_six_tables() -> None:
    """A parser that silently found none would make the test above pass for the wrong reason."""
    declared = parse_declared_tables(PROTOCOL.read_text(encoding="utf-8"))

    assert {"4.1", "4.2", "4.3", "4.4", "4.5", "4.6"} <= set(declared)


def test_the_parser_reports_a_prose_table_as_absent() -> None:
    """It must not borrow the next table's body when a heading has no table under it."""
    markdown = "\n".join(
        [
            "**Table 9.1 — Described in prose only**",
            "",
            "Some words and no table at all.",
            "",
            "**Table 9.2 — A real one**",
            "",
            "| Measure | Value |",
            "|---|---|",
            "| A | |",
        ]
    )

    declared = parse_declared_tables(markdown)

    assert "9.1" not in declared
    assert declared["9.2"][0] == ("Measure", "Value")


# --- Rendering ------------------------------------------------------------------------------


def test_a_declared_row_with_no_data_is_printed_as_pending_not_dropped() -> None:
    """Rule 4 applied to results tables: the row that failed is the row a reader needs."""
    rendered = render_table(TABLE_4_1, {}, stamp=STAMP)

    for disorder, band in TABLE_4_1.rows:
        assert f"| {disorder} | {band} | {PENDING} |" in rendered
    assert rendered.count(PENDING) == len(TABLE_4_1.rows) * len(TABLE_4_1.value_columns)


def test_filled_cells_appear_verbatim_and_the_rest_stay_pending() -> None:
    cells = {
        ("Ischemic stroke", "< 5"): {
            "n": "18",
            "Dice median [IQR]": "0.62 [0.51, 0.74] (n=18)",
            "Volume error ml, bias [95% LoA]": "+0.40 [-3.10, +3.90] (n=18)",
        }
    }

    rendered = render_table(TABLE_4_1, cells, stamp=STAMP)

    assert "| Ischemic stroke | < 5 | 18 | 0.62 [0.51, 0.74] (n=18) |" in rendered
    assert "+0.40 [-3.10, +3.90] (n=18)" in rendered
    assert "| Ischemic stroke | 5 to 25 |" in rendered


def test_the_header_and_separator_have_the_declared_column_count() -> None:
    rendered = render_table(TABLE_4_2, {}, stamp=STAMP)
    lines = rendered.splitlines()

    assert lines[0] == TABLE_4_2.heading
    assert lines[2] == "| " + " | ".join(TABLE_4_2.columns) + " |"
    assert lines[3].count("---") == len(TABLE_4_2.columns)


def test_the_bold_end_to_end_row_of_table_4_4_survives_rendering() -> None:
    """It is bold in ``docs/10`` because it is the headline number, so it stays bold here."""
    rendered = render_table(TABLE_4_4, {}, stamp=STAMP)

    assert "| **End to end** |" in rendered


# --- Version stamping -------------------------------------------------------------------


def test_every_rendered_table_carries_the_version_stamp() -> None:
    rendered = render_table(TABLE_4_2, {}, stamp=STAMP)

    assert "Model seg-0.1.0" in rendered
    assert "pipeline 0.1.0" in rendered
    assert "dataset ATLAS-v2.0" in rendered
    assert "split test-fold-0" in rendered


@pytest.mark.parametrize(
    "field",
    ["model_version", "pipeline_version", "dataset_version", "split_id"],
)
def test_an_empty_version_field_is_refused(field: str) -> None:
    """docs/10: a result with no version stamp is discarded. Better not to produce one."""
    fields = {
        "model_version": "seg-0.1.0",
        "pipeline_version": "0.1.0",
        "dataset_version": "ATLAS-v2.0",
        "split_id": "test-fold-0",
    }
    fields[field] = "   "

    with pytest.raises(TableError, match=field):
        VersionStamp(**fields)


# --- Refusals ---------------------------------------------------------------------------


def test_an_undeclared_row_key_is_refused() -> None:
    """Almost always a typo, and the alternative is a measured row silently showing PENDING."""
    with pytest.raises(TableError, match="no declared row"):
        render_table(TABLE_4_1, {("Ischemic stroke", "<5"): {"n": "18"}}, stamp=STAMP)


def test_an_undeclared_column_is_refused() -> None:
    with pytest.raises(TableError, match="unknown column"):
        render_table(
            TABLE_4_1,
            {("Ischemic stroke", "< 5"): {"Dice mean": "0.62"}},
            stamp=STAMP,
        )


def test_a_spec_with_no_value_columns_is_refused() -> None:
    with pytest.raises(TableError, match="key column"):
        TableSpec(
            number="9.9",
            title="Keys only",
            columns=("Measure",),
            rows=(("A",),),
            key_columns=1,
        )


def test_a_declared_row_with_the_wrong_number_of_key_cells_is_refused() -> None:
    with pytest.raises(TableError, match="key cells"):
        TableSpec(
            number="9.9",
            title="Mismatched",
            columns=("Disorder", "Size band (ml)", "n"),
            rows=(("Ischemic stroke",),),
            key_columns=2,
        )


# --- Writing ----------------------------------------------------------------------------


def test_write_table_creates_the_directory_and_returns_the_path(tmp_path: Path) -> None:
    target = tmp_path / "results" / "table-4-2.md"

    written = write_table(target, TABLE_4_2, {}, stamp=STAMP)

    assert written == target
    assert target.read_text(encoding="utf-8").startswith(TABLE_4_2.heading)


def test_write_all_writes_six_tables_including_the_empty_ones(tmp_path: Path) -> None:
    """A table that appears only once it has data is one nobody remembers is missing."""
    written = write_all(tmp_path, {}, stamp=STAMP)

    assert len(written) == len(ALL_TABLES)
    assert {path.name for path in written} == {
        "table-4-1.md",
        "table-4-2.md",
        "table-4-3.md",
        "table-4-4.md",
        "table-4-5.md",
        "table-4-6.md",
    }
    assert all(path.exists() for path in written)
