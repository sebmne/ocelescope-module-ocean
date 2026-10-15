"""V3: interval and event records have disjoint identifiers."""

from ocelescope_module_socel.infrastructure.conformance.context import ValidationContext
from ocelescope_module_socel.infrastructure.conformance.queries import summarize_query
from ocelescope_module_socel.infrastructure.conformance.result import Validation
from ocelescope_module_socel.infrastructure.conformance.rule import ValidationRule
from ocelescope_module_socel.infrastructure.schema import EVENT_RECORDS, INTERVAL_RECORDS


class DisjointRecordIdsRule(ValidationRule):
    code = "V3"
    requires = frozenset({"V1"})

    def validate(self, context: ValidationContext) -> Validation:
        summary = summarize_query(
            context.ocel,
            f"""
            SELECT record_id FROM {INTERVAL_RECORDS.name}
            INTERSECT
            SELECT record_id FROM {EVENT_RECORDS.name}
        """,
        )
        if not summary.count:
            return self.passed()
        return self.failed(
            f"{summary.count} record id(s) occur in both record tables; "
            f"examples: {summary.example_text}."
        )
