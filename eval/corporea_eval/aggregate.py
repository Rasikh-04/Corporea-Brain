"""Summarising metrics across a cohort, without losing the cases that failed.

``docs/10-EVALUATION_PROTOCOL.md``, statistical treatment:

- Medians and interquartile ranges, not means and standard deviations. Segmentation metrics
  are not normally distributed and a mean misrepresents them.
- Report n everywhere, including in table cells.
- **Report failures.** Cases the pipeline could not process are part of the result. Silently
  dropping them inflates every number in the table and is the easiest thing for an examiner
  to catch.

That last one is why this module exists rather than a call to ``np.median``. A list of
``MetricResult`` contains undefined values by design, and ``np.median`` over them either
raises or, worse, quietly produces a number from the ones that happened to work.
"""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass
from enum import Enum

import numpy as np

from .metrics import Degeneracy, MetricResult

__all__ = ["UndefinedPolicy", "Summary", "summarise"]


class UndefinedPolicy(Enum):
    """What to do about cases whose metric is undefined. There is no default worth having.

    ``EXCLUDE`` is the honest choice for a results table, but only because ``Summary`` carries
    ``n_undefined`` beside the median, so the exclusion is visible in the same cell.
    """

    EXCLUDE = "exclude"
    FAIL = "fail"


@dataclass(frozen=True)
class Summary:
    """A results-table cell, with everything needed to read it honestly.

    ``n_total`` and ``n_undefined`` sit next to the median because a median over 38 of 50
    cases is a different claim from a median over 50, and a table that shows only the former
    number invites the question that has no good answer.
    """

    name: str
    unit: str
    n_total: int
    n_undefined: int
    median: float | None
    iqr_low: float | None
    iqr_high: float | None
    degeneracies: dict[str, int]

    @property
    def n_used(self) -> int:
        return self.n_total - self.n_undefined

    def as_table_cell(self) -> str:
        """The ``median [IQR]`` form used by tables 4.1 to 4.3 in ``docs/10``."""
        if self.median is None:
            return f"no defined value (n={self.n_total})"
        cell = f"{self.median:.2f} [{self.iqr_low:.2f}, {self.iqr_high:.2f}] (n={self.n_used}"
        if self.n_undefined:
            cell += f" of {self.n_total}, {self.n_undefined} undefined"
        return cell + ")"


def summarise(
    results: Sequence[MetricResult],
    *,
    undefined: UndefinedPolicy,
) -> Summary:
    """Median and IQR over a cohort. ``undefined`` is keyword-only and has no default.

    Forcing the caller to name the policy is deliberate. The alternative is a default that
    drops failures, which is the exact behaviour ``docs/10`` singles out as the easiest thing
    for an examiner to catch.
    """
    if not results:
        raise ValueError("cannot summarise an empty result set; n is part of the answer")

    names = {result.name for result in results}
    if len(names) > 1:
        raise ValueError(f"refusing to mix metrics in one summary: {sorted(names)}")

    defined = [result for result in results if result.is_defined]
    n_undefined = len(results) - len(defined)

    if n_undefined and undefined is UndefinedPolicy.FAIL:
        raise ValueError(
            f"{n_undefined} of {len(results)} results are undefined and the policy is FAIL. "
            f"Degeneracies: {_count_degeneracies(results)}"
        )

    values = np.asarray([result.value for result in defined], dtype=np.float64)
    quartiles = np.percentile(values, [25.0, 50.0, 75.0]) if values.size else None

    return Summary(
        name=results[0].name,
        unit=results[0].unit,
        n_total=len(results),
        n_undefined=n_undefined,
        median=None if quartiles is None else float(quartiles[1]),
        iqr_low=None if quartiles is None else float(quartiles[0]),
        iqr_high=None if quartiles is None else float(quartiles[2]),
        degeneracies=_count_degeneracies(results),
    )


def _count_degeneracies(results: Sequence[MetricResult]) -> dict[str, int]:
    """Every degeneracy present, including ``none``. Rule 4: rank, never suppress."""
    counts = Counter(result.degeneracy for result in results)
    return {degeneracy.value: counts[degeneracy] for degeneracy in Degeneracy if counts[degeneracy]}
