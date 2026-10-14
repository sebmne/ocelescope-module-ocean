"""Flow quantification over time."""

from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from datetime import datetime

from ocelescope.ocel.constants.pm4py import EID_COL, TIMESTAMP_COL
from ocelescope.ocel.constants.tables import EVENTS_TABLE

from socel.domain import EventRecord, FlowInstance, FlowRecord, IntervalRecord
from socel.schema import EVENT_RECORDS, INTERVAL_RECORDS, SOCEL_END_TIME
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


@dataclass(frozen=True, slots=True)
class FlowWindowQuantity:
    """The quantity of a flow inside one window, summed over flow instances.

    ``inflow`` sums the shares of the records into the objects (positive),
    ``outflow`` those out of them (negative); ``quantity`` is their sum.
    """

    flow_id: str
    window: AnalysisWindow
    quantity: float
    inflow: float
    outflow: float


def flow_quantities(
    socel: SOCEL,
    windows: Sequence[AnalysisWindow],
    instances: Iterable[FlowInstance] | None = None,
) -> tuple[FlowWindowQuantity, ...]:
    """Return, per flow and window, the sum of ``quantity`` over flow instances.

    The same values as summing :func:`quantity` (Definition 6.1.2), computed in
    one query over all records instead of record by record, so it scales to
    large logs. ``instances`` limits the sum to those flow instances; ``None``
    takes every instance with records. Windows without a share are left out.
    """
    if not windows:
        return ()
    event_columns = {
        str(row[0])
        for row in socel.con.execute(f"DESCRIBE {identifier(EVENTS_TABLE)}").fetchall()
    }
    event_end = (
        f"event.{identifier(SOCEL_END_TIME)}"
        if SOCEL_END_TIME in event_columns
        else "NULL::TIMESTAMP"
    )
    if instances is None:
        counted, parameters = "SELECT * FROM record", {}
    else:
        listed = tuple(instances)
        counted = """
            SELECT * FROM record
            SEMI JOIN (
                SELECT unnest($objects) AS object_id, unnest($flows) AS flow_id
            ) chosen USING (object_id, flow_id)
        """
        parameters = {
            "objects": [instance.object_id for instance in listed],
            "flows": [instance.flow_id for instance in listed],
        }
    rows = socel.con.execute(
        f"""
        WITH window_ AS (
            SELECT unnest(range(len($starts))) AS id,
                   unnest($starts)::TIMESTAMP AS a, unnest($ends)::TIMESTAMP AS b
        ),
        -- span(r) (Definition 6.1.1): the interval, or the event's observed
        -- extent; an event-linked record without an end is a point (t is NULL).
        record AS (
            SELECT object_id, flow_id, quantity, start_time AS s, end_time AS t
            FROM {identifier(INTERVAL_RECORDS.name)}
            UNION ALL
            SELECT record.object_id, record.flow_id, record.quantity,
                   event.{identifier(TIMESTAMP_COL)}, {event_end}
            FROM {identifier(EVENT_RECORDS.name)} record
            JOIN {identifier(EVENTS_TABLE)} event
              ON event.{identifier(EID_COL)} = record.event_id
        ),
        counted AS ({counted}),
        -- share(r, w) for every record and window it has a share in.
        part AS (
            SELECT counted.flow_id, window_.id,
                   counted.quantity * epoch(least(t, b) - greatest(s, a)) / epoch(t - s)
                       AS quantity
            FROM counted JOIN window_ ON s < b AND t > a
            WHERE t IS NOT NULL
            UNION ALL
            SELECT counted.flow_id, window_.id, counted.quantity
            FROM counted JOIN window_ ON a <= s AND s < b
            WHERE t IS NULL
        )
        SELECT flow_id, id, sum(quantity),
               coalesce(sum(quantity) FILTER (quantity > 0), 0),
               coalesce(sum(quantity) FILTER (quantity < 0), 0)
        FROM part GROUP BY 1, 2 ORDER BY 1, 2
        """,
        {
            "starts": [window.start for window in windows],
            "ends": [window.end for window in windows],
            **parameters,
        },
    ).fetchall()
    return tuple(
        FlowWindowQuantity(
            str(flow_id),
            windows[int(window_id)],
            float(total),
            float(inflow),
            float(outflow),
        )
        for flow_id, window_id, total, inflow, outflow in rows
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
