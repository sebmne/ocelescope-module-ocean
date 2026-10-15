"""V10: flow categories and sOCEL classes belong to the sOCEL taxonomy."""

from collections.abc import Iterable

from ocelescope.ocel.constants.pm4py import (
    EID_COL,
    OBJECT_CHANGED_FIELD,
    OID_COL,
)
from ocelescope.ocel.constants.tables import EVENTS_TABLE, OBJECT_CHANGES_TABLE

from ocelescope_module_socel.domain.models.class_taxonomy import ClassNode
from ocelescope_module_socel.domain.taxonomies import TAXONOMY
from ocelescope_module_socel.infrastructure.conformance.context import ValidationContext
from ocelescope_module_socel.infrastructure.conformance.queries import identifier
from ocelescope_module_socel.infrastructure.conformance.result import Validation
from ocelescope_module_socel.infrastructure.conformance.rule import ValidationRule
from ocelescope_module_socel.infrastructure.schema import FLOW, SOCEL_CLASS


class TaxonomyMembershipRule(ValidationRule):
    """Require every assigned category and class to be a known taxonomy path."""

    code = "V10"
    requires = frozenset({"V1"})

    def validate(self, context: ValidationContext) -> Validation:
        messages = self._flow_messages(context)
        messages.extend(self._classification_messages(context))
        return self.from_messages(messages)

    @staticmethod
    def _flow_messages(context: ValidationContext) -> list[str]:
        rows = context.ocel.con.execute(
            f"""
            SELECT flow_id, category
            FROM {identifier(FLOW.name)}
            ORDER BY flow_id
            """
        ).fetchall()

        known = {path for root in TAXONOMY.flow_categories for path in root.paths()}
        missing = [str(flow_id) for flow_id, category in rows if category is None]
        unknown = [
            (str(flow_id), str(category))
            for flow_id, category in rows
            if category is not None and str(category) not in known
        ]

        messages: list[str] = []
        if missing:
            messages.append(
                f"{len(missing)} flow(s) have no category; "
                f"examples: {TaxonomyMembershipRule._examples(missing)}."
            )
        if unknown:
            messages.append(
                f"{len(unknown)} flow(s) use categories absent from the active "
                "flow taxonomy; examples: "
                f"{TaxonomyMembershipRule._assignments(unknown)}."
            )
        return messages

    @staticmethod
    def _classification_messages(context: ValidationContext) -> list[str]:
        messages: list[str] = []

        if SOCEL_CLASS in context.columns.get(EVENTS_TABLE, {}):
            rows = context.ocel.con.execute(
                f"""
                SELECT {identifier(EID_COL)}, {identifier(SOCEL_CLASS)}
                FROM {identifier(EVENTS_TABLE)}
                WHERE {identifier(SOCEL_CLASS)} IS NOT NULL
                ORDER BY {identifier(EID_COL)}
                """
            ).fetchall()
            messages.extend(
                TaxonomyMembershipRule._unknown_class_message(
                    rows,
                    TAXONOMY.event_classes,
                    "event",
                )
            )

        if SOCEL_CLASS in context.columns.get(OBJECT_CHANGES_TABLE, {}):
            rows = context.ocel.con.execute(
                f"""
                SELECT {identifier(OID_COL)}, {identifier(SOCEL_CLASS)}
                FROM {identifier(OBJECT_CHANGES_TABLE)}
                WHERE {identifier(OBJECT_CHANGED_FIELD)} = ?
                  AND {identifier(SOCEL_CLASS)} IS NOT NULL
                ORDER BY {identifier(OID_COL)}
                """,
                [SOCEL_CLASS],
            ).fetchall()
            messages.extend(
                TaxonomyMembershipRule._unknown_class_message(
                    rows,
                    TAXONOMY.object_classes,
                    "object",
                )
            )

        return messages

    @staticmethod
    def _unknown_class_message(
        rows: Iterable[tuple[object, ...]],
        taxonomy: tuple[ClassNode, ...],
        element: str,
    ) -> list[str]:
        known = {path for root in taxonomy for path in root.paths()}
        unknown = [
            (str(element_id), str(class_name))
            for element_id, class_name in rows
            if str(class_name) not in known
        ]
        if not unknown:
            return []
        return [
            (
                f"{len(unknown)} {element} classification(s) are absent from the "
                f"active {element}-class taxonomy; examples: "
                f"{TaxonomyMembershipRule._assignments(unknown)}."
            )
        ]

    @staticmethod
    def _examples(values: Iterable[str], limit: int = 3) -> str:
        return ", ".join(list(values)[:limit])

    @staticmethod
    def _assignments(values: Iterable[tuple[str, str]], limit: int = 3) -> str:
        return ", ".join(f"{element_id}={value!r}" for element_id, value in list(values)[:limit])
