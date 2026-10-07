"""Flow quantification over time."""

from dataclasses import dataclass
from datetime import datetime

from ocelescope.ocel.constants.pm4py import EID_COL, TIMESTAMP_COL
from ocelescope.ocel.constants.tables import EVENTS_TABLE

from socel.domain import EventRecord, FlowInstance, FlowRecord, IntervalRecord
from socel.schema import SOCEL_END_TIME
from socel.socel import SOCEL
from socel.validation.queries import identifier


@dataclass(frozen=True, slots=True)
class AnalysisWindow:
    """A half-open analysis interval ``[start, end)``."""

    start: datetime
    end: datetime

    def __post_init__(self) -> None:
        try:
            valid = self.start < self.end
        except TypeError as error:
            raise ValueError(
                "Analysis-window timestamps must use compatible time zones."
            ) from error
        if not valid:
            raise ValueError("An analysis window must start before it ends.")

    def contains(self, timestamp: datetime) -> bool:
        """Whether ``timestamp`` lies in this half-open window."""
        return self.start <= timestamp < self.end


def share(socel: SOCEL, record: FlowRecord, window: AnalysisWindow) -> float:
    """Return the share of one record observed inside ``window``."""
    match record:
        case IntervalRecord(_, _, quantity, start, end):
            return _duration_share(
                quantity,
                start,
                end,
                window,
            )
        case EventRecord(_, _, quantity, event_id):
            start, end = _event_span(socel, event_id)
            if end is None:
                return quantity if window.contains(start) else 0.0
            return _duration_share(quantity, start, end, window)


def quantity(
    socel: SOCEL,
    instance: FlowInstance,
    window: AnalysisWindow,
) -> float:
    """Return the quantity of a flow instance observed inside ``window``."""
    return sum(
        (
            share(socel, record, window)
            for record in socel.measurements.for_instance(instance)
        ),
        start=0.0,
    )


def _duration_share(
    quantity: float,
    start: datetime,
    end: datetime,
    window: AnalysisWindow,
) -> float:
    overlap_start = max(start, window.start)
    overlap_end = min(end, window.end)
    if overlap_start >= overlap_end:
        return 0.0
    overlap_fraction = (overlap_end - overlap_start) / (end - start)
    return quantity * overlap_fraction


def _event_span(socel: SOCEL, event_id: str) -> tuple[datetime, datetime | None]:
    event_columns = {
        str(row[0])
        for row in socel.con.execute(f"DESCRIBE {identifier(EVENTS_TABLE)}").fetchall()
    }
    end_projection = (
        identifier(SOCEL_END_TIME) if SOCEL_END_TIME in event_columns else "NULL"
    )
    row = socel.con.execute(
        f"""
        SELECT {identifier(TIMESTAMP_COL)}, {end_projection}
        FROM {identifier(EVENTS_TABLE)}
        WHERE {identifier(EID_COL)} = ?
        """,
        [event_id],
    ).fetchone()
    if row is None:
        raise KeyError(f"Unknown event {event_id!r}.")

    start, end = row
    if not isinstance(start, datetime):
        raise TypeError(f"Event {event_id!r} does not have a datetime timestamp.")
    if end is not None and not isinstance(end, datetime):
        raise TypeError(f"Event {event_id!r} does not have a datetime end timestamp.")
    return start, end
