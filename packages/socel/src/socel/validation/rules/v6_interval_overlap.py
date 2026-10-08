"""V6: interval records of one flow instance do not overlap."""

from socel.schema import INTERVAL_RECORDS
from socel.validation.context import ValidationContext
from socel.validation.queries import summarize_query
from socel.validation.rule import RuleValidation, ValidationRule


class IntervalOverlapRule(ValidationRule):
    code = "V6"
    requires = frozenset({"V1", "V4"})

    def validate(self, context: ValidationContext) -> RuleValidation:
        # A record overlaps another exactly when, with the instance's records in
        # the order they start, it starts before the latest end among those
        # before it. One sorted pass per instance finds that; comparing every
        # record with every other takes seconds on a month of meter readings.
        summary = summarize_query(
            context.ocel,
            f"""
            SELECT earlier_record_id, record_id
            FROM (
                SELECT
                    record_id,
                    start_time,
                    max(end_time) OVER earlier AS earlier_end,
                    arg_max(record_id, end_time) OVER earlier AS earlier_record_id
                FROM {INTERVAL_RECORDS.name}
                WINDOW earlier AS (
                    PARTITION BY flow_id, object_id
                    ORDER BY start_time, end_time, record_id
                    ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING
                )
            )
            WHERE start_time < earlier_end
        """,
        )
        if not summary.count:
            return self.passed()
        return self.failed(
            f"{summary.count} interval record(s) overlap an earlier one within one "
            f"flow instance; examples: {summary.example_text}."
        )
