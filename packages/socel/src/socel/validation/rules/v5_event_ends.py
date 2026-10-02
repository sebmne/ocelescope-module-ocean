"""V5: each observed event end is strictly after the event start."""

from ocelescope.ocel.constants.pm4py import EID_COL, TIMESTAMP_COL

from socel.schema import SOCEL_END_TIME
from socel.validation.context import ValidationContext
from socel.validation.queries import identifier, summarize_query
from socel.validation.rule import RuleValidation, ValidationRule


class ValidEventEndsRule(ValidationRule):
    code = "V5"
    requires = frozenset({"V1"})

    def validate(self, context: ValidationContext) -> RuleValidation:
        if SOCEL_END_TIME not in context.columns.get("events", {}):
            return self.passed()

        summary = summarize_query(
            context.ocel,
            f"""
            SELECT {identifier(EID_COL)}
            FROM events
            WHERE {SOCEL_END_TIME} IS NOT NULL
              AND {SOCEL_END_TIME} <= {identifier(TIMESTAMP_COL)}
        """,
        )
        if not summary.count:
            return self.passed()
        return self.failed(
            f"{summary.count} event(s) do not end after they start; "
            f"examples: {summary.example_text}."
        )
