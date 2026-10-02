"""V2: all referenced flows, objects, and events exist."""

from dataclasses import dataclass

from ocelescope.ocel.constants.pm4py import EID_COL, OID_COL

from socel.schema import CONTAINED_IN, EVENT_RECORDS, FLOW, INTERVAL_RECORDS
from socel.validation.context import ValidationContext
from socel.validation.queries import identifier, summarize_query
from socel.validation.rule import RuleValidation, ValidationRule


@dataclass(frozen=True)
class Reference:
    source_table: str
    source_column: str
    target_table: str
    target_column: str


REFERENCES = (
    Reference(INTERVAL_RECORDS.name, "flow_id", FLOW.name, "flow_id"),
    Reference(INTERVAL_RECORDS.name, "object_id", "objects", OID_COL),
    Reference(EVENT_RECORDS.name, "flow_id", FLOW.name, "flow_id"),
    Reference(EVENT_RECORDS.name, "object_id", "objects", OID_COL),
    Reference(EVENT_RECORDS.name, "event_id", "events", EID_COL),
    Reference(CONTAINED_IN.name, "flow_id", FLOW.name, "flow_id"),
    Reference(CONTAINED_IN.name, "object_id", "objects", OID_COL),
    Reference(CONTAINED_IN.name, "parent_object_id", "objects", OID_COL),
)


class ReferencesRule(ValidationRule):
    code = "V2"
    requires = frozenset({"V1"})

    def validate(self, context: ValidationContext) -> RuleValidation:
        messages: list[str] = []
        for reference in REFERENCES:
            summary = summarize_query(context.ocel, self._query(reference))
            if summary.count:
                messages.append(
                    f"{reference.source_table}.{reference.source_column} contains "
                    f"{summary.count} value(s) absent from "
                    f"{reference.target_table}.{reference.target_column}; "
                    f"examples: {summary.example_text}."
                )
        return self.from_messages(messages)

    @staticmethod
    def _query(reference: Reference) -> str:
        return f"""
            SELECT DISTINCT source.{identifier(reference.source_column)}
            FROM {identifier(reference.source_table)} AS source
            WHERE NOT EXISTS (
                SELECT 1 FROM {identifier(reference.target_table)} AS target
                WHERE target.{identifier(reference.target_column)} =
                      source.{identifier(reference.source_column)}
            )
        """
