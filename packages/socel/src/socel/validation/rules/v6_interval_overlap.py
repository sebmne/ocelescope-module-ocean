"""V6: interval records of one flow instance do not overlap."""

from socel.schema import INTERVAL_RECORDS
from socel.validation.context import ValidationContext
from socel.validation.queries import summarize_query
from socel.validation.rule import RuleValidation, ValidationRule


class IntervalOverlapRule(ValidationRule):
    code = "V6"
    requires = frozenset({"V1", "V4"})

    def validate(self, context: ValidationContext) -> RuleValidation:
        summary = summarize_query(
            context.ocel,
            f"""
            SELECT first.record_id, second.record_id
            FROM {INTERVAL_RECORDS.name} AS first
            JOIN {INTERVAL_RECORDS.name} AS second
              ON first.flow_id = second.flow_id
             AND first.object_id = second.object_id
             AND first.record_id < second.record_id
             AND first.start_time < second.end_time
             AND second.start_time < first.end_time
        """,
        )
        if not summary.count:
            return self.passed()
        return self.failed(
            f"{summary.count} pair(s) of interval records overlap within one flow "
            f"instance; examples: {summary.example_text}."
        )
