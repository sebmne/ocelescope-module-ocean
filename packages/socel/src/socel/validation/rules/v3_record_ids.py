"""V3: interval and event records have disjoint identifiers."""

from socel.schema import EVENT_RECORDS, INTERVAL_RECORDS
from socel.validation.context import ValidationContext
from socel.validation.queries import summarize_query
from socel.validation.rule import RuleValidation, ValidationRule


class DisjointRecordIdsRule(ValidationRule):
    code = "V3"
    requires = frozenset({"V1"})

    def validate(self, context: ValidationContext) -> RuleValidation:
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
