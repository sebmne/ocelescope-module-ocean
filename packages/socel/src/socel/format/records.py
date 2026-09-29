"""The flow records FR = IR ∪ ER as one relation, each with its span (Definition
6.1.1) - the reading the model and the analysis share."""

from ocelescope import OCEL

from socel.format.attributes import events_sql
from socel.format.schema import EVENT_RECORDS, INTERVAL_RECORDS


def records_sql(ocel: OCEL) -> str:
    """record_id, kind ("interval" or "event"), flow_id, object_id, quantity,
    start_time, end_time, event_id. An event-linked record spans its event;
    end_time is null for a point event. Requires the record tables."""
    return f"""
        SELECT record_id, 'interval' AS kind, flow_id, object_id, quantity,
               start_time, end_time, NULL::VARCHAR AS event_id
        FROM {INTERVAL_RECORDS.name}
        UNION ALL
        SELECT r.record_id, 'event', r.flow_id, r.object_id, r.quantity,
               e.time, e.end_time, r.event_id
        FROM {EVENT_RECORDS.name} r
        LEFT JOIN ({events_sql(ocel)}) e ON e.event_id = r.event_id
    """
