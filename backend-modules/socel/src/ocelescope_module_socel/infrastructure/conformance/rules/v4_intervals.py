"""V4: every interval record starts strictly before it ends."""

from ocelescope_module_socel.infrastructure.conformance.context import ValidationContext
from ocelescope_module_socel.infrastructure.conformance.queries import summarize_query
from ocelescope_module_socel.infrastructure.conformance.result import Validation
from ocelescope_module_socel.infrastructure.conformance.rule import ValidationRule
from ocelescope_module_socel.infrastructure.schema import INTERVAL_RECORDS


class ValidIntervalsRule(ValidationRule):
    code = "V4"
    requires = frozenset({"V1"})

    def validate(self, context: ValidationContext) -> Validation:
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
