from collections.abc import Sequence

from duckdb import DuckDBPyConnection
from ocelescope import OCEL

from ocelescope_module_socel.domain.models.flow_edit import FlowEdit
from ocelescope_module_socel.infrastructure.schema import (
    CONTAINED_IN,
    EVENT_RECORDS,
    FLOW,
    INTERVAL_RECORDS,
)

# The tables that name a flow, and those of them that hold quantities.
_NAMING = (FLOW.name, INTERVAL_RECORDS.name, EVENT_RECORDS.name, CONTAINED_IN.name)
_RECORDS = (INTERVAL_RECORDS.name, EVENT_RECORDS.name)


class DuckDbFlowEditor:
    """Flow edits as SQL on the log's DuckDB database: a few statements per
    flow, none per record."""

    def flow_ids(self, ocel: OCEL) -> set[str]:
        exists = ocel.sql(
            "SELECT 1 FROM duckdb_tables() WHERE database_name = current_database() "
            "AND schema_name = current_schema() AND table_name = ?",
            params=[FLOW.name],
        ).fetchone()
        if not exists:
            return set()
        return {row[0] for row in ocel.sql(f"SELECT flow_id FROM {FLOW.name}").fetchall()}

    def edit(self, ocel: OCEL, edits: Sequence[FlowEdit]) -> None:
        con = ocel.con
        for edit in edits:
            if edit.delete:
                for table in _NAMING:
                    con.execute(f"DELETE FROM {table} WHERE flow_id = ?", [edit.flow_id])
                continue
            if edit.conversion is not None:
                for table in _RECORDS:
                    con.execute(
                        f"UPDATE {table} SET quantity = quantity * ? WHERE flow_id = ?",
                        [edit.conversion, edit.flow_id],
                    )
            con.execute(
                f"UPDATE {FLOW.name} SET unit = ?, category = ?, external_ref = ? "
                "WHERE flow_id = ?",
                [edit.unit, edit.category, edit.external_ref, edit.flow_id],
            )
        # Renamed in two steps, through names no flow has, so that two flows
        # can swap their names.
        renamed = [e for e in edits if not e.delete and e.name != e.flow_id]
        for step, edit in enumerate(renamed):
            _rename(con, edit.flow_id, f"\0renaming {step}")
        for step, edit in enumerate(renamed):
            _rename(con, f"\0renaming {step}", edit.name)


def _rename(con: DuckDBPyConnection, old: str, new: str) -> None:
    for table in _NAMING:
        con.execute(f"UPDATE {table} SET flow_id = ? WHERE flow_id = ?", [new, old])
