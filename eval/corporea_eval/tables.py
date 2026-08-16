"""The results tables, written by the harness in the exact form that goes into the thesis.

``docs/10-EVALUATION_PROTOCOL.md`` on the harness: "**Writes the results table
automatically**, in the exact format that goes into the thesis. Hand-transcribing numbers into
a document is how numbers drift." And on the tables themselves: "Fill these. Do not redesign
them late."

Both sentences are load-bearing, and they pull in different directions unless something holds
them together. This module is that something: the six table layouts are declared here as data,
and ``eval/tests/test_tables_match_the_protocol.py`` parses ``docs/10`` and asserts that the
column headers and the declared row labels are identical to the ones in the document. So a
table cannot be quietly redesigned in either place. Change one, the gate fails until the other
matches.

Three properties the renderer has, each for a reason
-----------------------------------------------------
**Every declared row is always printed.** A row with no data renders as ``PENDING``, never as
an absent line. Rule 4, rank never suppress, applies to results tables most of all: the size
band the segmenter could not handle is the row a reader most needs to see, and it is exactly
the row that a "skip empty rows" renderer would drop.

**No row renders without a version stamp.** ``docs/10`` requires the model, pipeline and
dataset versions and the split identifier on every result row, and says a result with no
version stamp is discarded. Here the stamp is a required argument, so an unstamped table is
not something that can be produced and then noticed later.

**Cells are strings, produced upstream.** ``Summary.as_table_cell`` and
``BlandAltman.as_table_cell`` already know how to render themselves honestly, including the
``n`` and the count of undefined cases. This module does no arithmetic at all, so there is no
second place where a number can be rounded, and no way for the table to disagree with the
summary it came from.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Final

__all__ = [
    "PENDING",
    "ALL_TABLES",
    "TABLE_4_1",
    "TABLE_4_2",
    "TABLE_4_3",
    "TABLE_4_4",
    "TABLE_4_5",
    "TABLE_4_6",
    "TableError",
    "TableSpec",
    "VersionStamp",
    "render_table",
    "write_table",
]

# What an unfilled cell says. Not an empty string: an empty cell in a rendered results table
# is ambiguous between "not measured yet", "measured as zero" and "the renderer dropped it".
# A word rather than a dash, because a dash is also the heading separator and the minus sign,
# and a cell marker has to be greppable without matching either.
PENDING: Final[str] = "pending"


class TableError(ValueError):
    """A table was asked to render something its declared shape does not allow."""


@dataclass(frozen=True)
class VersionStamp:
    """What every result row is stamped with, per ``docs/10``: no stamp, no result.

    All four fields are required and there are no defaults. A default here would be a version
    string that is wrong on the first day somebody forgets to pass one, and a wrong version
    stamp is worse than none: it makes an unreproducible number look reproducible.
    """

    model_version: str
    pipeline_version: str
    dataset_version: str
    split_id: str

    def __post_init__(self) -> None:
        for name, value in (
            ("model_version", self.model_version),
            ("pipeline_version", self.pipeline_version),
            ("dataset_version", self.dataset_version),
            ("split_id", self.split_id),
        ):
            if not value.strip():
                raise TableError(
                    f"{name} is empty. docs/10 requires the model, pipeline and dataset "
                    f"versions and the split identifier on every result row, and says a "
                    f"result with no version stamp is discarded."
                )

    def render(self) -> str:
        """The footnote line printed under every rendered table."""
        return (
            f"Model {self.model_version} · pipeline {self.pipeline_version} · "
            f"dataset {self.dataset_version} · split {self.split_id}"
        )


@dataclass(frozen=True)
class TableSpec:
    """One results table's declared shape: its columns and the rows it must always show.

    ``key_columns`` is how many leading columns identify a row rather than report a number.
    Table 4.1 is keyed on disorder *and* size band, the rest on one column each.
    """

    number: str
    title: str
    columns: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    key_columns: int

    def __post_init__(self) -> None:
        if self.key_columns < 1 or self.key_columns >= len(self.columns):
            raise TableError(
                f"table {self.number}: key_columns={self.key_columns} against "
                f"{len(self.columns)} columns; a table needs at least one key column and at "
                f"least one value column"
            )
        for row in self.rows:
            if len(row) != self.key_columns:
                raise TableError(
                    f"table {self.number}: declared row {row} has {len(row)} key cells, "
                    f"expected {self.key_columns}"
                )

    @property
    def value_columns(self) -> tuple[str, ...]:
        """The columns a caller supplies values for."""
        return self.columns[self.key_columns :]

    @property
    def heading(self) -> str:
        """The bold heading line as it appears in ``docs/10`` and in the rendered output."""
        return f"**Table {self.number} — {self.title}**"


# The six tables, transcribed from docs/10-EVALUATION_PROTOCOL.md#tables. The transcription is
# not trusted: test_tables_match_the_protocol.py re-reads that document and fails if a single
# header or row label here has drifted from it.

TABLE_4_1: Final[TableSpec] = TableSpec(
    number="4.1",
    title="Segmentation performance, by disorder and lesion size band (E1)",
    columns=(
        "Disorder",
        "Size band (ml)",
        "n",
        "Dice median [IQR]",
        "HD95 mm median [IQR]",
        "ASSD mm median [IQR]",
        "Volume error ml, bias [95% LoA]",
    ),
    rows=(
        ("Ischemic stroke", "< 5"),
        ("Ischemic stroke", "5 to 25"),
        ("Ischemic stroke", "> 25"),
        ("Glioma, whole tumour", "all"),
        ("Glioma, tumour core", "all"),
        ("Glioma, enhancing", "all"),
    ),
    key_columns=2,
)

TABLE_4_2: Final[TableSpec] = TableSpec(
    number="4.2",
    title="Region attribution agreement against expert reading (E2)",
    columns=(
        "Region category",
        "n cases",
        "System-identified",
        "Expert-identified",
        "Both",
        "Agreement %",
        "Cohen's kappa",
    ),
    rows=(
        ("Frontal",),
        ("Temporal",),
        ("Parietal",),
        ("Occipital",),
        ("Deep grey",),
        ("Brainstem, cerebellum",),
        ("White matter tract",),
    ),
    key_columns=1,
)

TABLE_4_3: Final[TableSpec] = TableSpec(
    number="4.3",
    title="Longitudinal change detection (E3)",
    columns=(
        "Measure",
        "n pairs",
        "Test-retest CV %",
        "Minimum detectable change",
        "Sensitivity to known change",
    ),
    rows=(
        ("Lesion volume",),
        ("Involved region count",),
    ),
    key_columns=1,
)

TABLE_4_4: Final[TableSpec] = TableSpec(
    number="4.4",
    title="Resource and offline compliance (E4)",
    columns=(
        "Stage",
        "Wall time s, median [range]",
        "Peak RAM MB",
        "Peak VRAM MB",
    ),
    rows=(
        ("Ingest and classify",),
        ("Convert and de-identify",),
        ("Preprocess",),
        ("Parcellation",),
        ("Segmentation",),
        ("Attribution",),
        ("**End to end**",),
    ),
    key_columns=1,
)

TABLE_4_5: Final[TableSpec] = TableSpec(
    number="4.5",
    title="Expert usefulness rubric (E5)",
    columns=(
        "Rubric item",
        "n cases",
        "m clinicians",
        "Mean [SD]",
    ),
    rows=(
        ("Findings are complete",),
        ("Findings are correctly ranked",),
        ("Region attribution is defensible",),
        ("Uncertainty is communicated",),
        ("Would use in a review meeting",),
    ),
    key_columns=1,
)

TABLE_4_6: Final[TableSpec] = TableSpec(
    number="4.6",
    title="Usability",
    columns=(
        "Measure",
        "n participants",
        "Value",
    ),
    rows=(
        ("SUS mean [SD]",),
        ("Task completion rate",),
        ("Median task time",),
    ),
    key_columns=1,
)

ALL_TABLES: Final[tuple[TableSpec, ...]] = (
    TABLE_4_1,
    TABLE_4_2,
    TABLE_4_3,
    TABLE_4_4,
    TABLE_4_5,
    TABLE_4_6,
)


def render_table(
    spec: TableSpec,
    cells: Mapping[tuple[str, ...], Mapping[str, str]],
    *,
    stamp: VersionStamp,
) -> str:
    """Render one results table as GitHub-flavoured markdown, ready to paste into the thesis.

    ``cells`` is keyed by the row's key cells — ``("Ischemic stroke", "< 5")`` for table 4.1 —
    and each value maps a value column name to an already-rendered string.

    Refuses two things rather than guessing at them:

    - A key that is not a declared row. Almost always a typo in a row label, and the failure
      it would otherwise cause is a table that silently reports ``PENDING`` for a row that was
      in fact measured.
    - A column name that is not in the spec. Same reasoning, one level down.

    Does not refuse a *missing* value column: a partially filled table is the normal state of
    this document for most of the project, and the missing cells print as ``PENDING`` where a
    reader can see them.
    """
    declared = set(spec.rows)
    for key in cells:
        if key not in declared:
            raise TableError(
                f"table {spec.number} has no declared row {key!r}. Declared rows are "
                f"{sorted(declared)}. docs/10: do not redesign the tables late."
            )
    allowed = set(spec.value_columns)
    for key, row in cells.items():
        unknown = sorted(set(row) - allowed)
        if unknown:
            raise TableError(
                f"table {spec.number}, row {key!r}: unknown column(s) {unknown}. "
                f"Value columns are {list(spec.value_columns)}."
            )

    lines = [
        spec.heading,
        "",
        "| " + " | ".join(spec.columns) + " |",
        "|" + "|".join(["---"] * len(spec.columns)) + "|",
    ]
    for key in spec.rows:
        values = cells.get(key, {})
        rendered = [values.get(column, PENDING) for column in spec.value_columns]
        lines.append("| " + " | ".join([*key, *rendered]) + " |")
    lines += ["", stamp.render()]
    return "\n".join(lines) + "\n"


def write_table(
    path: Path,
    spec: TableSpec,
    cells: Mapping[tuple[str, ...], Mapping[str, str]],
    *,
    stamp: VersionStamp,
) -> Path:
    """Render and write one table, creating the parent directory if it does not exist.

    Returns the path written, so a caller can log it. Overwrites: a results table is derived
    from a run and is regenerated, never edited, which is the point of generating it.
    """
    rendered = render_table(spec, cells, stamp=stamp)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(rendered, encoding="utf-8")
    return path


def write_all(
    directory: Path,
    cells_by_table: Mapping[str, Mapping[tuple[str, ...], Mapping[str, str]]],
    *,
    stamp: VersionStamp,
) -> tuple[Path, ...]:
    """Write all six tables to ``directory``, including the ones with nothing in them yet.

    An empty table is written rather than skipped, for the same reason an empty row is
    printed rather than dropped: the results chapter has six tables in it on the day it is
    submitted, and a table that appears only once it has data is one nobody remembers is
    missing.
    """
    written: list[Path] = []
    for spec in ALL_TABLES:
        written.append(
            write_table(
                directory / f"table-{spec.number.replace('.', '-')}.md",
                spec,
                cells_by_table.get(spec.number, {}),
                stamp=stamp,
            )
        )
    return tuple(written)


def parse_declared_tables(
    markdown: str,
) -> dict[str, tuple[tuple[str, ...], list[tuple[str, ...]]]]:
    """Pull ``**Table N — title**`` headings and their tables out of ``docs/10``'s markdown.

    Lives here rather than in the test because it is the definition of what "the table in the
    document" means, and a test that carried its own parser could be made to pass by loosening
    the parser instead of by fixing the disagreement.

    Returns, per table number, the column headers and every body row's cells.
    """
    tables: dict[str, tuple[tuple[str, ...], list[tuple[str, ...]]]] = {}
    lines = markdown.splitlines()
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not (stripped.startswith("**Table ") and " — " in stripped):
            continue
        number = stripped.removeprefix("**Table ").split(" — ", 1)[0].strip()
        header, body = _read_table_after(lines, index)
        if header:
            tables[number] = (header, body)
    return tables


def _read_table_after(
    lines: Sequence[str],
    index: int,
) -> tuple[tuple[str, ...], list[tuple[str, ...]]]:
    """The header cells and body rows of the next markdown table after ``index``.

    Gives up rather than searching past the following heading, so a table declared in prose
    with no markdown table under it reports as absent instead of borrowing the next one's.
    """
    cursor = index + 1
    while cursor < len(lines) and not lines[cursor].strip().startswith("|"):
        if lines[cursor].strip().startswith("**Table "):
            return (), []
        cursor += 1
    if cursor >= len(lines):
        return (), []
    header = _split_row(lines[cursor])
    cursor += 2  # skip the |---|---| separator
    body: list[tuple[str, ...]] = []
    while cursor < len(lines) and lines[cursor].strip().startswith("|"):
        body.append(_split_row(lines[cursor]))
        cursor += 1
    return header, body


def _split_row(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))
