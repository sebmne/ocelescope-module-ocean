"""V4: every interval record starts strictly before it ends."""

from socel.schema import INTERVAL_RECORDS
from socel.validation.context import ValidationContext
from socel.validation.queries import summarize_query
from socel.validation.rule import RuleValidation, ValidationRule


class ValidIntervalsRule(ValidationRule):
    code = "V4"
    requires = frozenset({"V1"})

    def validate(self, context: ValidationContext) -> RuleValidation:
        summary = summarize_query(
            context.ocel,
            f"""
            SELECT record_id FROM {INTERVAL_RECORDS.name}
            WHERE start_time >= end_time
        """,
        )
        if not summary.count:
            return self.passed()
        return self.failed(
            f"{summary.count} interval record(s) do not start before they end; "
            f"examples: {summary.example_text}."
        )
