"""V9: flow-instance containment is acyclic."""

from ocelescope_module_socel.infrastructure.conformance.context import ValidationContext
from ocelescope_module_socel.infrastructure.conformance.queries import summarize_query
from ocelescope_module_socel.infrastructure.conformance.result import Validation
from ocelescope_module_socel.infrastructure.conformance.rule import ValidationRule
from ocelescope_module_socel.infrastructure.schema import CONTAINED_IN


class AcyclicContainmentRule(ValidationRule):
    code = "V9"
    requires = frozenset({"V1"})

    def validate(self, context: ValidationContext) -> Validation:
        summary = summarize_query(
            context.ocel,
            f"""
            WITH RECURSIVE walk(flow_id, origin, current, depth) AS (
                SELECT flow_id, object_id, parent_object_id, 1
                FROM {CONTAINED_IN.name}
                UNION ALL
                SELECT walk.flow_id, walk.origin, edge.parent_object_id, walk.depth + 1
                FROM walk
                JOIN {CONTAINED_IN.name} AS edge
                  ON edge.flow_id = walk.flow_id
                 AND edge.object_id = walk.current
                WHERE walk.current <> walk.origin
                  AND walk.depth <= (SELECT count(*) FROM {CONTAINED_IN.name})
            )
            SELECT DISTINCT flow_id, origin
            FROM walk
            WHERE current = origin
        """,
        )
        if not summary.count:
            return self.passed()
        return self.failed(
            f"Containment contains {summary.count} flow instance(s) on a cycle; "
            f"examples: {summary.example_text}."
        )
