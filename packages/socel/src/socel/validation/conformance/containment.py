import polars as pl
from ocelescope import OCEL

from socel.format.schema import CONTAINED_IN
from socel.validation.check import RowCheck, counted


class ContainmentIsAcyclic(RowCheck):
    """V9: no flow instance is, directly or through others, contained in itself.

    Walks each flow instance up its chain of parents; one that comes back to
    where it started lies on a cycle. An object contained in itself (the
    table's CHECK constraint) is the shortest such cycle. Each instance has at
    most one parent (V1), so the walk is a chain and ends after at most as many
    steps as there are rows.
    """

    id = "V9"
    title = "Containment is acyclic"
    requires = ("V1",)

    def query(self, ocel: OCEL) -> str:
        return f"""
            WITH RECURSIVE walk(flow_id, object_id, reached, steps) AS (
                SELECT flow_id, object_id, parent_object_id, 1 FROM {CONTAINED_IN.name}
                UNION ALL
                SELECT w.flow_id, w.object_id, c.parent_object_id, w.steps + 1
                FROM walk w
                JOIN {CONTAINED_IN.name} c ON c.flow_id = w.flow_id AND c.object_id = w.reached
                WHERE w.reached <> w.object_id
                  AND w.steps < (SELECT count(*) FROM {CONTAINED_IN.name})
            )
            SELECT DISTINCT flow_id, object_id, steps AS cycle_length
            FROM walk WHERE reached = object_id
            ORDER BY flow_id, object_id
        """

    def describe(self, rows: pl.DataFrame) -> str:
        instances = counted(rows.height, "flow instance")
        flows = counted(rows["flow_id"].n_unique(), "flow")
        return f"{instances} on a containment cycle, in {flows}."
