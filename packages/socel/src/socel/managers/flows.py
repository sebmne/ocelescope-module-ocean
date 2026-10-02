"""Navigate the sustainability flows declared by an sOCEL."""

from ocelescope.ocel.managers.base import BaseManager

from socel.domain import Flow
from socel.schema import FLOW


class FlowsManager(BaseManager):
    """Query flow definitions without exposing their physical table."""

    def all(self) -> tuple[Flow, ...]:
        """Return every declared flow, ordered by identifier."""
        rows = self._relation(
            f"""
            SELECT flow_id, unit, category, external_ref
            FROM {FLOW.name}
            ORDER BY flow_id
            """
        ).fetchall()
        return tuple(self._flow(row) for row in rows)

    def get(self, flow_id: str) -> Flow | None:
        """Return the flow with ``flow_id``, if it exists."""
        row = self._relation(
            f"""
            SELECT flow_id, unit, category, external_ref
            FROM {FLOW.name}
            WHERE flow_id = ?
            """,
            [flow_id],
        ).fetchone()
        return self._flow(row) if row else None

    def by_category(self, category: str) -> tuple[Flow, ...]:
        """Return the flows assigned to ``category``."""
        rows = self._relation(
            f"""
            SELECT flow_id, unit, category, external_ref
            FROM {FLOW.name}
            WHERE category = ?
            ORDER BY flow_id
            """,
            [category],
        ).fetchall()
        return tuple(self._flow(row) for row in rows)

    @staticmethod
    def _flow(row: tuple[object, ...]) -> Flow:
        flow_id, unit, category, external_ref = row
        if not isinstance(flow_id, str) or not isinstance(unit, str):
            raise TypeError("A stored flow must have string identifiers and units.")
        return Flow(
            id=flow_id,
            unit=unit,
            category=category if isinstance(category, str) else None,
            external_ref=external_ref if isinstance(external_ref, str) else None,
        )
