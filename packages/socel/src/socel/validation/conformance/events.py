"""Events in time, and event-linked records against interval records.

An event with a socel_end_time covers [time, socel_end_time); without one it is a
point at its time. An event-linked record must not report what an interval
record of the same flow instance already covers - that would count it twice.
"""

import polars as pl
from ocelescope import OCEL

from socel.format.attributes import events_sql
from socel.format.schema import EVENT_RECORDS, INTERVAL_RECORDS
from socel.validation.check import RowCheck, counted


def event_spans(ocel: OCEL) -> str:
    """SQL for every event: event_id, start (its time) and end (null for a point)."""
    return f'SELECT event_id, time AS "start", end_time AS "end" FROM ({events_sql(ocel)})'


def records_against_intervals(ocel: OCEL, condition: str) -> str:
    """SQL pairing event-linked records with the interval records of their flow
    instance for which `condition` holds; `e` is the event, `i` the interval record."""
    return f"""
        SELECT r.record_id, r.object_id, r.flow_id, r.event_id,
               e."start" AS event_start, e."end" AS event_end,
               i.record_id AS interval_record_id, i.start_time, i.end_time
        FROM {EVENT_RECORDS.name} r
        JOIN ({event_spans(ocel)}) e ON e.event_id = r.event_id
        JOIN {INTERVAL_RECORDS.name} i ON i.object_id = r.object_id AND i.flow_id = r.flow_id
        WHERE {condition}
        ORDER BY r.object_id, r.flow_id, e."start"
    """


class EventEndAfterStart(RowCheck):
    """V5: an event's socel_end_time, where set, lies strictly after its time."""

    id = "V5"
    title = "Every event with an end time ends after it starts"
    requires = ("V1",)

    def query(self, ocel: OCEL) -> str:
        return f'SELECT * FROM ({event_spans(ocel)}) WHERE "end" IS NOT NULL AND "end" <= "start"'

    def describe(self, rows: pl.DataFrame) -> str:
        return f"{counted(rows.height, 'event')} not ending after it starts."


class DurationEventsDoNotOverlap(RowCheck):
    """V7: an event-linked record whose event has a duration does not overlap an
    interval record of the same flow instance."""

    id = "V7"
    title = "Records of events with a duration do not overlap interval records"
    requires = ("V1",)

    def query(self, ocel: OCEL) -> str:
        return records_against_intervals(
            ocel, 'e."end" IS NOT NULL AND e."start" < i.end_time AND i.start_time < e."end"'
        )

    def describe(self, rows: pl.DataFrame) -> str:
        records = counted(rows["record_id"].n_unique(), "event-linked record")
        return f"{records} overlapping interval records of the same flow instance."


class PointEventsOutsideIntervals(RowCheck):
    """V8: an event-linked record whose event is a point does not fall within an
    interval record of the same flow instance."""

    id = "V8"
    title = "Records of point events do not fall within interval records"
    requires = ("V1",)

    def query(self, ocel: OCEL) -> str:
        return records_against_intervals(
            ocel, 'e."end" IS NULL AND i.start_time <= e."start" AND e."start" < i.end_time'
        )

    def describe(self, rows: pl.DataFrame) -> str:
        records = counted(rows["record_id"].n_unique(), "event-linked record")
        return f"{records} within interval records of the same flow instance."
