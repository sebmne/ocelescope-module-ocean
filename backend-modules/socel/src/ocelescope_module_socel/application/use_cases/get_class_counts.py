from collections import Counter

from socel import SOCEL, Classification

from ocelescope_module_socel.domain.models.class_counts import ClassCount, ClassCounts


class GetClassCounts:
    """How many objects and events carry each sOCEL class, most frequent first;
    the unclassified ones under None."""

    def __init__(self, *, socel: SOCEL) -> None:
        self._socel = socel

    def execute(self) -> ClassCounts:
        socel = self._socel
        classes = socel.classifications
        return ClassCounts(
            objects=_counts(classes.objects(), classes.handling_units(), socel.ocel.objects.count),
            events=_counts(classes.events(), classes.operations(), socel.ocel.events.count),
        )


def _counts(
    classified: tuple[Classification, ...], core: tuple[Classification, ...], total: int
) -> tuple[ClassCount, ...]:
    """Counts per class; `core` are the classifications that make handling units
    (objects) or operations (events)."""
    core_classes = {classification.name for classification in core}
    counts: Counter[str | None] = Counter(classification.name for classification in classified)
    if total > len(classified):
        counts[None] = total - len(classified)
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0] is None, item[0] or ""))
    return tuple(
        ClassCount(socel_class=name, count=count, is_core=name in core_classes)
        for name, count in ordered
    )
