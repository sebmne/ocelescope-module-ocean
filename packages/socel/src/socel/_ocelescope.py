"""Where the sOCEL meets Ocelescope's OCEL: the one module that knows its internals.

Ocelescope holds an OCEL as flat DuckDB tables whose names and columns differ
from the OCEL 2.0 SQLite serialization the thesis refers to. This module maps
between the two, so the rest of the package speaks the thesis' language.
"""

from datetime import datetime

import duckdb
from ocelescope import OCEL
from ocelescope.ocel.constants.pm4py import (
    ACTIVITY_COL,
    EID_COL,
    OBJECT_CHANGED_FIELD,
    OID_COL,
    OTYPE_COL,
    TIMESTAMP_COL,
)
from ocelescope.util.sql import ident, literal, utc_timestamp

__all__ = [
    "ACTIVITY",
    "E2O",
    "EID",
    "EPOCH",
    "EVENTS",
    "FIELD",
    "OBJECTS",
    "OBJECT_CHANGES",
    "OBJECT_TYPE",
    "OID",
    "TIME",
    "column_type",
    "has_column",
    "has_table",
    "ident",
    "is_read_only",
    "literal",
    "reference_target",
    "utc_timestamp",
]

EVENTS, OBJECTS, OBJECT_CHANGES, E2O = "events", "objects", "object_changes", "e2o"
EID, OID, TIME = EID_COL, OID_COL, TIMESTAMP_COL
ACTIVITY, OBJECT_TYPE, FIELD = ACTIVITY_COL, OTYPE_COL, OBJECT_CHANGED_FIELD

# An OCEL 2.0 object's initial attribute values carry this time: Ocelescope reads
# them as rows of `object_changes` at the epoch, and writes such rows back as
# initial values (with no changed field).
EPOCH = datetime(1970, 1, 1)

# The SQLite base tables a foreign key can reference, as Ocelescope holds them.
_BASE_TABLES = {"object": (OBJECTS, OID), "event": (EVENTS, EID)}


def reference_target(table: str, column: str) -> tuple[str, str]:
    """The DuckDB table and column behind a reference in the SQLite schema."""
    return _BASE_TABLES.get(table, (table, column))


def is_read_only(ocel: OCEL) -> bool:
    """Whether the OCEL's database cannot be written, like the ones the backend hands out."""
    row = ocel.con.execute(
        "SELECT readonly FROM duckdb_databases() WHERE database_name = current_database()"
    ).fetchone()
    return bool(row and row[0])


def has_table(ocel: OCEL, table: str) -> bool:
    return _table_columns(ocel.con, table) != {}


def has_column(ocel: OCEL, table: str, column: str) -> bool:
    return column in _table_columns(ocel.con, table)


def column_type(ocel: OCEL, table: str, column: str) -> str | None:
    """The DuckDB type of a column, or None if there is no such column."""
    return _table_columns(ocel.con, table).get(column)


def _table_columns(con: duckdb.DuckDBPyConnection, table: str) -> dict[str, str]:
    rows = con.execute(
        "SELECT column_name, data_type FROM information_schema.columns "
        "WHERE table_schema = 'main' AND table_name = ?",
        [table],
    ).fetchall()
    return {str(name): str(data_type) for name, data_type in rows}
