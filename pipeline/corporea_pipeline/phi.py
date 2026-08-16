"""The PHI-in-logs assertion: the third cross-cutting test, and the cheapest of the three.

``docs/12-SECURITY_PRIVACY_COMPLIANCE.md``, logging hygiene: "The most common way student
projects leak PHI is the log file." And the check it asks for: "A test asserts that a full
pipeline run on a PHI-seeded synthetic study produces a log containing none of the seeded
values. This is cheap and it is the check that actually works."

Cheap, and the check that actually works, because the alternative is reading every logging
call in the repository forever. This one runs a study whose identifiers are known and greps
the output for them, so a leak introduced by a debug line somebody adds at eleven at night
fails the commit gate rather than shipping.

Why an exact substring search is not enough
--------------------------------------------
A scanner that looks for the literal seeded string gives confident, wrong assurance. The way
PHI actually reaches a log is *reformatted*: a date of birth seeded as ``1974-03-02`` arrives
as ``02/03/1974`` from a DICOM header, or ``19740302`` from a filename; a phone number seeded
with spaces arrives with dashes; a name seeded as ``Doe^Jane`` arrives as ``Jane Doe`` or as
the surname alone in a path. Every one of those is a leak and none of them is a substring
match.

So each seeded field expands into the forms it is plausibly written in, and the scan looks for
all of them. Numbers are compared digit-only, which catches every separator convention at once
rather than enumerating them.

What is deliberately *not* flagged
-----------------------------------
The opaque case identifier and artifact identifiers are what ``docs/12`` says logs are *for*:
"Log the opaque case identifier and the artifact identifier. Never the value." A scanner that
flagged those would be flagging correct code, and a check that fires on correct code is a
check somebody turns off. ``test_a_log_of_only_the_case_id_is_clean`` holds that line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from enum import StrEnum
from typing import Final

__all__ = [
    "MIN_NEEDLE_LENGTH",
    "PhiFinding",
    "PhiLeakError",
    "PhiNeedle",
    "NeedleKind",
    "SeededStudy",
    "SEEDED_STUDY",
    "assert_no_phi",
    "scan_for_phi",
]

# Shorter than this and a needle matches by accident: a two-character surname fragment or a
# three-digit MRN tail will hit ordinary log text and the assertion becomes noise somebody
# suppresses. Anything this short has to be caught by the full-value needle instead.
MIN_NEEDLE_LENGTH: Final[int] = 4


class NeedleKind(StrEnum):
    """How a needle is matched against the haystack."""

    # Case-insensitive, on word boundaries. For names, places and free text.
    TEXT = "text"
    # Digits only, on both sides, so every separator convention matches at once. For phone
    # numbers, medical record numbers and dates written as digit runs.
    DIGITS = "digits"


@dataclass(frozen=True)
class PhiNeedle:
    """One form one seeded field might be written in.

    ``form`` names the shape rather than showing it: ``"date, DD/MM/YYYY"``, not the date. The
    needle travels into failure messages and failure messages go into logs, and a PHI scanner
    whose own output is PHI has solved nothing.
    """

    field: str
    form: str
    value: str
    kind: NeedleKind

    def search(self, haystack: str) -> int:
        """How many times this form appears in ``haystack``."""
        if self.kind is NeedleKind.DIGITS:
            digits = _digits(self.value)
            if len(digits) < MIN_NEEDLE_LENGTH:
                return 0
            return sum(run.count(digits) for run in _digit_runs(haystack))
        return len(re.findall(_bounded(self.value), haystack, flags=re.IGNORECASE))


@dataclass(frozen=True)
class PhiFinding:
    """A leak, named without being repeated.

    Carries the field and the form, never the matched text. This object is what gets printed
    when the assertion fails, and printing the value would write the PHI into the CI log of
    the run that caught it leaking into a log.
    """

    field: str
    form: str
    count: int

    def describe(self) -> str:
        return f"{self.field} ({self.form}) appears {self.count} time(s)"


class PhiLeakError(AssertionError):
    """Seeded PHI reached an output that must never contain it.

    An ``AssertionError`` for the same reason ``OrientationError`` is: this is never caught
    and handled. A run that leaks PHI has no valid output.
    """


@dataclass(frozen=True)
class SeededStudy:
    """A synthetic study with known PHI in every field ``docs/12`` names as identified.

    Every value here is invented and belongs to nobody. That is the whole point: the assertion
    needs values it can search for exhaustively, which is impossible with real data and
    forbidden with patient data by rule 8.

    ``case_id`` is the opposite of the rest. It is the opaque identifier that ``docs/12``
    requires logs to use, so it is carried here to be asserted *present* in a well-behaved
    log, not absent.
    """

    case_id: str
    patient_name_dicom: str
    given_name: str
    family_name: str
    mother_family_name: str
    address: str
    facility: str
    phone: str
    birth_date: date
    mrn: str
    study_description: str
    series_description: str
    source_path: str

    def needles(self) -> tuple[PhiNeedle, ...]:
        """Every form each seeded field is plausibly written in.

        The name expands to the DICOM caret form, the two components separately, and the two
        natural orderings, because a log line is as likely to carry ``Jane Doe`` as anything
        the header actually held. The date expands to the four orderings a DICOM header, a
        filename and a European or American locale produce between them.
        """
        needles: list[PhiNeedle] = [
            PhiNeedle("patient_name", "DICOM caret form", self.patient_name_dicom, NeedleKind.TEXT),
            PhiNeedle("patient_name", "family name", self.family_name, NeedleKind.TEXT),
            PhiNeedle("patient_name", "given name", self.given_name, NeedleKind.TEXT),
            PhiNeedle(
                "patient_name",
                "given then family",
                f"{self.given_name} {self.family_name}",
                NeedleKind.TEXT,
            ),
            PhiNeedle(
                "patient_name",
                "family then given",
                f"{self.family_name} {self.given_name}",
                NeedleKind.TEXT,
            ),
            PhiNeedle(
                "mother_family_name", "family name", self.mother_family_name, NeedleKind.TEXT
            ),
            PhiNeedle("address", "as recorded", self.address, NeedleKind.TEXT),
            PhiNeedle("facility", "as recorded", self.facility, NeedleKind.TEXT),
            PhiNeedle("phone", "digits, any separators", self.phone, NeedleKind.DIGITS),
            PhiNeedle("mrn", "as recorded", self.mrn, NeedleKind.TEXT),
            PhiNeedle("mrn", "digits, any separators", self.mrn, NeedleKind.DIGITS),
            PhiNeedle("study_description", "free text", self.study_description, NeedleKind.TEXT),
            PhiNeedle("series_description", "free text", self.series_description, NeedleKind.TEXT),
            PhiNeedle("source_path", "as recorded", self.source_path, NeedleKind.TEXT),
        ]
        needles += [
            PhiNeedle("birth_date", form, value, NeedleKind.DIGITS)
            for form, value in _date_forms(self.birth_date)
        ]
        return tuple(needle for needle in needles if len(needle.value.strip()) >= MIN_NEEDLE_LENGTH)


# The study the commit gate runs against. Values invented, and deliberately distinctive: a
# surname that is also an ordinary English word would make every finding ambiguous.
SEEDED_STUDY: Final[SeededStudy] = SeededStudy(
    case_id="CASE-0001",
    patient_name_dicom="Vasquez-Ferrand^Ingrid",
    given_name="Ingrid",
    family_name="Vasquez-Ferrand",
    mother_family_name="Okonkwo-Baptiste",
    address="14 Rue Mistral, Toulouse",
    facility="Saint Aidan Regional Infirmary",
    phone="+44 7700 900412",
    birth_date=date(1974, 3, 2),
    mrn="RXH0093471",
    study_description="MRI BRAIN Ingrid Vasquez-Ferrand follow up",
    series_description="AX T1 POST Vasquez-Ferrand",
    source_path="/exports/VASQUEZ-FERRAND_19740302/study-1/series-3",
)


def scan_for_phi(text: str, study: SeededStudy = SEEDED_STUDY) -> tuple[PhiFinding, ...]:
    """Every seeded value that appears in ``text``, in any of its plausible written forms.

    Reports all findings rather than stopping at the first. Rule 4: one leak found and fixed
    while three others sit in the same commit is the worst possible outcome of a scan, because
    the run afterwards is green and the reader believes it.
    """
    findings = [
        PhiFinding(needle.field, needle.form, count)
        for needle in study.needles()
        if (count := needle.search(text)) > 0
    ]
    return tuple(findings)


def assert_no_phi(text: str, study: SeededStudy = SEEDED_STUDY, *, source: str = "output") -> None:
    """Raise ``PhiLeakError`` if any seeded value reached ``text``.

    ``source`` names what was scanned — a log, a provenance sidecar, an exported report — so
    that the failure says where to look. It does not name the value, and neither does the
    message.
    """
    findings = scan_for_phi(text, study)
    if not findings:
        return
    raise PhiLeakError(
        f"seeded PHI reached {source}. On real data this is a disclosure, and the values "
        f"below are named but not repeated, because a message quoting them would write the "
        f"PHI into the log of the run that caught it:\n"
        + "\n".join(f"  {finding.describe()}" for finding in findings)
    )


def _date_forms(value: date) -> tuple[tuple[str, str], ...]:
    """The digit orderings a date of birth arrives in, from a header, a filename or a locale.

    Three, not four: separators are removed before comparison, so ``1974-03-02`` and
    ``19740302`` are the same needle and listing both would report one leak twice.
    """
    return (
        ("date, year first", value.strftime("%Y%m%d")),
        ("date, day first", value.strftime("%d%m%Y")),
        ("date, month first", value.strftime("%m%d%Y")),
    )


def _bounded(value: str) -> str:
    """``value`` as a regex that will not match inside a longer word, and will not miss.

    ``\\b`` is the obvious choice here and it is wrong twice.

    It **misses**, because ``_`` is a word character to ``\\b``. DICOM export directories are
    named ``SURNAME_19740302`` almost by convention, so the single most common way a name
    reaches a log is through a string where ``\\b`` finds no boundary at all. The guard here
    treats only letters and digits as word characters, so the underscore ends the name.

    It also misses whenever the value itself begins or ends with punctuation — a source path
    starting ``/`` — because ``\\b`` needs a word character on one side of the position and
    there is none. The guard is therefore applied per edge, and only where the edge is
    alphanumeric enough for it to mean anything.
    """
    left = "(?<![0-9A-Za-z])" if value[:1].isalnum() else ""
    right = "(?![0-9A-Za-z])" if value[-1:].isalnum() else ""
    return left + re.escape(value) + right


def _digits(text: str) -> str:
    return re.sub(r"\D", "", text)


def _digit_runs(text: str) -> list[str]:
    """Digit sequences, with the separators that appear *inside* numbers removed.

    Not ``_digits(whole_document)``. Stripping every non-digit from the entire text welds
    unrelated numbers together, so a log line reading ``case 1974 step 0302`` would produce
    ``19740302`` and report a date of birth that is not there. A false positive on this
    assertion is not harmless: it is the kind of finding that gets the check disabled.

    A run may span spaces, dashes, dots, slashes, parentheses and a leading plus, because a
    phone number written ``+44 7700 900412`` is one number. It may not span a letter.
    """
    return [re.sub(r"\D", "", match.group(0)) for match in re.finditer(r"\d[\d\s\-./()+]*\d", text)]
