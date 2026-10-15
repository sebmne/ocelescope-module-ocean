"""V7: duration-based event records do not overlap interval records."""

from ocelescope.ocel.constants.pm4py import EID_COL, TIMESTAMP_COL

from ocelescope_module_socel.infrastructure.conformance.context import ValidationContext
from ocelescope_module_socel.infrastructure.conformance.queries import identifier, summarize_query
from ocelescope_module_socel.infrastructure.conformance.result import Validation
from ocelescope_module_socel.infrastructure.conformance.rule import ValidationRule
from ocelescope_module_socel.infrastructure.schema import (
    EVENT_RECORDS,
    INTERVAL_RECORDS,
    SOCEL_END_TIME,
)


class DurationOverlapRule(ValidationRule):
    code = "V7"
    requires = frozenset({"V1", "V2", "V4", "V5"})

    def validate(self, context: ValidationContext) -> Validation:
        if SOCEL_END_TIME not in context.columns.get("events", {}):
            return self.passed()

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
            WHERE event.{SOCEL_END_TIME} IS NOT NULL
              AND event.{identifier(TIMESTAMP_COL)} < interval.end_time
              AND interval.start_time < event.{SOCEL_END_TIME}
        """,
        )
        if not summary.count:
            return self.passed()
        return self.failed(
            f"{summary.count} duration-based event record/interval pair(s) overlap; "
            f"examples: {summary.example_text}."
        )
