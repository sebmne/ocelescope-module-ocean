"""Navigate the measurements recorded for flow instances."""

from datetime import datetime

from ocelescope.ocel.managers.base import BaseManager

from socel.domain import EventRecord, FlowInstance, FlowRecord, IntervalRecord
from socel.schema import EVENT_RECORDS, INTERVAL_RECORDS


class MeasurementsManager(BaseManager):
    """Expose flow records independently of their storage representation."""

    def all(self) -> tuple[FlowRecord, ...]:
        """Return all interval-based and event-linked records."""
        return self._records()

    def for_instance(self, instance: FlowInstance) -> tuple[FlowRecord, ...]:
        """Return the measurements belonging to ``instance``."""
        return self._records(instance)

    def for_event(self, event_id: str) -> tuple[FlowRecord, ...]:
        """Return the measurements directly linked to an OCEL event."""
        rows = self._relation(
            f"""
            SELECT record_id, object_id, flow_id, quantity, event_id
            FROM {EVENT_RECORDS.name}
            WHERE event_id = ?
            ORDER BY record_id
            """,
            [event_id],
        ).fetchall()
        return tuple(self._event_record(row) for row in rows)

    def _records(self, instance: FlowInstance | None = None) -> tuple[FlowRecord, ...]:
        conditions = "WHERE object_id = ? AND flow_id = ?" if instance else ""
        params: list[object] | None = (
            [instance.object_id, instance.flow_id] if instance else None
        )
        interval_rows = self._relation(
            f"""
            SELECT record_id, object_id, flow_id, quantity, start_time, end_time
            FROM {INTERVAL_RECORDS.name}
            {conditions}
            """,
            params,
        ).fetchall()
        event_rows = self._relation(
            f"""
            SELECT record_id, object_id, flow_id, quantity, event_id
            FROM {EVENT_RECORDS.name}
            {conditions}
            """,
            params,
        ).fetchall()
        records: list[FlowRecord] = [
            self._interval_record(row) for row in interval_rows
        ]
        records.extend(self._event_record(row) for row in event_rows)
        return tuple(sorted(records, key=lambda record: record.id))

    @staticmethod
    def _interval_record(row: tuple[object, ...]) -> IntervalRecord:
        record_id, object_id, flow_id, quantity, start, end = row
        if not isinstance(record_id, str):
            raise TypeError("A flow-record identifier must be a string.")
        if not isinstance(object_id, str) or not isinstance(flow_id, str):
            raise TypeError("A flow record must contain string identifiers.")
        if not isinstance(quantity, int | float):
            raise TypeError("A flow-record quantity must be numeric.")
        if not isinstance(start, datetime) or not isinstance(end, datetime):
            raise TypeError("An interval record must contain timestamps.")
        return IntervalRecord(
            id=record_id,
            instance=FlowInstance(object_id=object_id, flow_id=flow_id),
            quantity=float(quantity),
            start=start,
            end=end,
        )

    @staticmethod
    def _event_record(row: tuple[object, ...]) -> EventRecord:
        record_id, object_id, flow_id, quantity, event_id = row
        if not isinstance(record_id, str) or not isinstance(event_id, str):
            raise TypeError("An event-record identifier must be a string.")
        if not isinstance(object_id, str) or not isinstance(flow_id, str):
            raise TypeError("An event record must contain string identifiers.")
        if not isinstance(quantity, int | float):
            raise TypeError("A flow-record quantity must be numeric.")
        return EventRecord(
            id=record_id,
            instance=FlowInstance(object_id=object_id, flow_id=flow_id),
            quantity=float(quantity),
            event_id=event_id,
        )
