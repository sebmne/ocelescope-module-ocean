"""Navigate flow instances and their containment hierarchy."""

from ocelescope.ocel.managers.base import BaseManager

from socel.domain import FlowInstance
from socel.schema import CONTAINED_IN, EVENT_RECORDS, INTERVAL_RECORDS

_FLOW_INSTANCES = f"""
    SELECT object_id, flow_id FROM {INTERVAL_RECORDS.name}
    UNION
    SELECT object_id, flow_id FROM {EVENT_RECORDS.name}
    UNION
    SELECT object_id, flow_id FROM {CONTAINED_IN.name}
    UNION
    SELECT parent_object_id AS object_id, flow_id FROM {CONTAINED_IN.name}
"""


class FlowInstancesManager(BaseManager):
    """Manage the formal ``(object, flow)`` pairs of an sOCEL."""

    def all(self) -> tuple[FlowInstance, ...]:
        """Return all flow instances represented in the sOCEL."""
        return self._find()

    def get(self, object_id: str, flow_id: str) -> FlowInstance | None:
        """Return a flow instance if the pair occurs in the sOCEL."""
        instances = self._find(object_id=object_id, flow_id=flow_id)
        return instances[0] if instances else None

    def for_object(self, object_id: str) -> tuple[FlowInstance, ...]:
        """Return all flows observed at one OCEL object."""
        return self._find(object_id=object_id)

    def for_flow(self, flow_id: str) -> tuple[FlowInstance, ...]:
        """Return all object-specific instances of one flow."""
        return self._find(flow_id=flow_id)

    def parent(self, instance: FlowInstance) -> FlowInstance | None:
        """Return the directly containing flow instance, if any."""
        row = self._relation(
            f"""
            SELECT parent_object_id, flow_id
            FROM {CONTAINED_IN.name}
            WHERE object_id = ? AND flow_id = ?
            """,
            [instance.object_id, instance.flow_id],
        ).fetchone()
        return self._flow_instance(row) if row else None

    def children(self, instance: FlowInstance) -> tuple[FlowInstance, ...]:
        """Return the flow instances directly contained in ``instance``."""
        rows = self._relation(
            f"""
            SELECT object_id, flow_id
            FROM {CONTAINED_IN.name}
            WHERE parent_object_id = ? AND flow_id = ?
            ORDER BY object_id
            """,
            [instance.object_id, instance.flow_id],
        ).fetchall()
        return tuple(self._flow_instance(row) for row in rows)

    def ancestors(self, instance: FlowInstance) -> tuple[FlowInstance, ...]:
        """Return containing instances from nearest to furthest."""
        rows = self._relation(
            f"""
            WITH RECURSIVE ancestors(object_id, flow_id, depth) AS (
                SELECT parent_object_id, flow_id, 1
                FROM {CONTAINED_IN.name}
                WHERE object_id = ? AND flow_id = ?
                UNION ALL
                SELECT edge.parent_object_id, edge.flow_id, ancestors.depth + 1
                FROM ancestors
                JOIN {CONTAINED_IN.name} AS edge
                  ON edge.object_id = ancestors.object_id
                 AND edge.flow_id = ancestors.flow_id
            )
            SELECT object_id, flow_id
            FROM ancestors
            ORDER BY depth
            """,
            [instance.object_id, instance.flow_id],
        ).fetchall()
        return tuple(self._flow_instance(row) for row in rows)

    def descendants(self, instance: FlowInstance) -> tuple[FlowInstance, ...]:
        """Return all transitively contained instances."""
        rows = self._relation(
            f"""
            WITH RECURSIVE descendants(object_id, flow_id, depth) AS (
                SELECT object_id, flow_id, 1
                FROM {CONTAINED_IN.name}
                WHERE parent_object_id = ? AND flow_id = ?
                UNION ALL
                SELECT edge.object_id, edge.flow_id, descendants.depth + 1
                FROM descendants
                JOIN {CONTAINED_IN.name} AS edge
                  ON edge.parent_object_id = descendants.object_id
                 AND edge.flow_id = descendants.flow_id
            )
            SELECT object_id, flow_id
            FROM descendants
            ORDER BY depth, object_id
            """,
            [instance.object_id, instance.flow_id],
        ).fetchall()
        return tuple(self._flow_instance(row) for row in rows)

    def roots(self, flow_id: str | None = None) -> tuple[FlowInstance, ...]:
        """Return instances that are not contained in another instance."""
        flow_filter = "AND instances.flow_id = ?" if flow_id is not None else ""
        params: list[object] | None = [flow_id] if flow_id is not None else None
        rows = self._relation(
            f"""
            SELECT instances.object_id, instances.flow_id
            FROM ({_FLOW_INSTANCES}) AS instances
            WHERE NOT EXISTS (
                SELECT 1
                FROM {CONTAINED_IN.name} AS edge
                WHERE edge.object_id = instances.object_id
                  AND edge.flow_id = instances.flow_id
            )
            {flow_filter}
            ORDER BY instances.flow_id, instances.object_id
            """,
            params,
        ).fetchall()
        return tuple(self._flow_instance(row) for row in rows)

    def _find(
        self, *, object_id: str | None = None, flow_id: str | None = None
    ) -> tuple[FlowInstance, ...]:
        conditions: list[str] = []
        params: list[object] = []
        if object_id is not None:
            conditions.append("object_id = ?")
            params.append(object_id)
        if flow_id is not None:
            conditions.append("flow_id = ?")
            params.append(flow_id)
        where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
        rows = self._relation(
            f"""
            SELECT object_id, flow_id
            FROM ({_FLOW_INSTANCES}) AS instances
            {where}
            ORDER BY flow_id, object_id
            """,
            params or None,
        ).fetchall()
        return tuple(self._flow_instance(row) for row in rows)

    @staticmethod
    def _flow_instance(row: tuple[object, ...]) -> FlowInstance:
        object_id, flow_id = row
        if not isinstance(object_id, str) or not isinstance(flow_id, str):
            raise TypeError("A flow instance must contain string identifiers.")
        return FlowInstance(object_id=object_id, flow_id=flow_id)
