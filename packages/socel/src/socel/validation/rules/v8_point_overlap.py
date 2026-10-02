"""V8: point-event records do not fall within interval records."""

from ocelescope.ocel.constants.pm4py import EID_COL, TIMESTAMP_COL

from socel.schema import EVENT_RECORDS, INTERVAL_RECORDS, SOCEL_END_TIME
from socel.validation.context import ValidationContext
from socel.validation.queries import identifier, summarize_query
from socel.validation.rule import RuleValidation, ValidationRule


class PointOverlapRule(ValidationRule):
    code = "V8"
    requires = frozenset({"V1", "V2", "V4"})

    def validate(self, context: ValidationContext) -> RuleValidation:
        event_end = (
            f"event.{SOCEL_END_TIME}"
            if SOCEL_END_TIME in context.columns.get("events", {})
            else "NULL"
        )
        summary = summarize_query(
            context.ocel,
            f"""
            SELECT record.record_id, interval.record_id
            FROM {EVENT_RECORDS.name} AS record
            JOIN events AS event
              ON event.{identifier(EID_COL)} = record.event_id
            JOIN {INTERVAL_RECORDS.name} AS interval
              ON interval.flow_id = record.flow_id
             AND interval.object_id = record.object_id
            WHERE {event_end} IS NULL
              AND interval.start_time <= event.{identifier(TIMESTAMP_COL)}
              AND event.{identifier(TIMESTAMP_COL)} < interval.end_time
        """,
        )
        if not summary.count:
            return self.passed()
        return self.failed(
            f"{summary.count} point-event record/interval pair(s) overlap; "
            f"examples: {summary.example_text}."
        )
