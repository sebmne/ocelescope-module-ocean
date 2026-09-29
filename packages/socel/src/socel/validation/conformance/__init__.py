"""The sOCEL conformance contract: the thesis' rules V1–V9 (Appendix A.2).

A log that passes all of them conforms, provided its base is valid OCEL 2.0;
anything these rules do not decide is a quality question, not conformance.
"""

from socel.validation.conformance.containment import ContainmentIsAcyclic
from socel.validation.conformance.events import (
    DurationEventsDoNotOverlap,
    EventEndAfterStart,
    PointEventsOutsideIntervals,
)
from socel.validation.conformance.intervals import IntervalsAreValid, IntervalsDoNotOverlap
from socel.validation.conformance.references import RecordIdsDisjoint, ReferencesExist
from socel.validation.conformance.structure import TablesAndColumns
from socel.validation.profile import Profile

CONFORMANCE = Profile(
    "sOCEL conformance (V1–V9)",
    (
        TablesAndColumns(),  # V1
        ReferencesExist(),  # V2
        RecordIdsDisjoint(),  # V3
        IntervalsAreValid(),  # V4
        EventEndAfterStart(),  # V5
        IntervalsDoNotOverlap(),  # V6
        DurationEventsDoNotOverlap(),  # V7
        PointEventsOutsideIntervals(),  # V8
        ContainmentIsAcyclic(),  # V9
    ),
)

__all__ = [
    "CONFORMANCE",
    "ContainmentIsAcyclic",
    "DurationEventsDoNotOverlap",
    "EventEndAfterStart",
    "IntervalsAreValid",
    "IntervalsDoNotOverlap",
    "PointEventsOutsideIntervals",
    "RecordIdsDisjoint",
    "ReferencesExist",
    "TablesAndColumns",
]
