from dataclasses import dataclass

import polars as pl
from ocelescope import OCEL
from socel import SOCEL

from ocelescope_module_socel.overview.domain.models.class_counts import ClassCount, ClassCounts


@dataclass(frozen=True, kw_only=True)
class GetClassCountsCommand:
    ocel_id: str


class GetClassCounts:
    """How many objects and events carry each socel_class, most frequent first.
    Works on any OCEL: the classes are attributes, not sOCEL tables."""

    def __init__(self, *, ocel: OCEL) -> None:
        self._ocel = ocel

    def execute(self, command: GetClassCountsCommand) -> ClassCounts:
        socel = SOCEL(self._ocel)
        return ClassCounts(
            objects=_counts(socel.objects, "is_handling_unit"),
            events=_counts(socel.events, "is_operation"),
        )


def _counts(entities: pl.LazyFrame, core: str) -> tuple[ClassCount, ...]:
    counts = (
        entities.group_by("socel_class")
        .agg(pl.len().alias("count"), pl.col(core).any().alias("is_core"))
        .sort(["count", "socel_class"], descending=[True, False], nulls_last=True)
        .collect()
    )
    return tuple(
        ClassCount(socel_class=row["socel_class"], count=row["count"], is_core=row["is_core"])
        for row in counts.iter_rows(named=True)
    )
