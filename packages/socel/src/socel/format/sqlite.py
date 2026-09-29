"""The four sOCEL tables in the SQLite serialization: reading them in, writing them out.

Ocelescope itself copies every further table of an SQLite log into the OCEL
(promi4s/ocelescope#458), but reads timestamps without their offsets and writes
tables without their constraints, empty tables not at all. So the sOCEL tables
are read again here, with timestamps in UTC, and written as the thesis declares
them (Appendix A.1). The OCEL 2.0 base tables, and the reserved attributes with
them, are Ocelescope's.
"""

import sqlite3
from contextlib import closing
from pathlib import Path

from ocelescope import OCEL

from socel._ocelescope import has_column, has_table, ident, literal, utc_timestamp
from socel.errors import SocelWriteError
from socel.format.schema import TABLES, Column

_SOURCE = "socel_source"
_BATCH_SIZE = 50_000


def read_tables(source: Path, ocel: OCEL) -> None:
    """Copies the sOCEL tables of the SQLite file into the OCEL's database.

    Every column is read as text and cast to its declared type; timestamps in any
    ISO 8601 offset become UTC, like Ocelescope's own. Values that do not cast
    become null, which the conformance checks report. Tables or columns the file
    lacks stay absent, for the same reason.
    """
    con = ocel.con
    con.execute("INSTALL sqlite; LOAD sqlite;")
    con.execute("SET sqlite_all_varchar = true")
    con.execute(f"ATTACH {literal(str(source))} AS {_SOURCE} (TYPE sqlite, READ_ONLY)")
    try:
        present: dict[str, set[str]] = {}
        for table, column in con.execute(
            "SELECT table_name, column_name FROM information_schema.columns "
            "WHERE table_catalog = ?",
            [_SOURCE],
        ).fetchall():
            present.setdefault(str(table), set()).add(str(column))

        for table in TABLES:
            if table.name not in present:
                continue
            columns = [column for column in table.columns if column.name in present[table.name]]
            values = ", ".join(f"{_read(column)} AS {ident(column.name)}" for column in columns)
            con.execute(
                f"CREATE OR REPLACE TABLE {ident(table.name)} AS "
                f"SELECT {values} FROM {_SOURCE}.{ident(table.name)}"
            )
    finally:
        con.execute(f"DETACH {_SOURCE}")
        con.execute("SET sqlite_all_varchar = false")


def write_tables(ocel: OCEL, target: Path) -> None:
    """Adds the four sOCEL tables to an OCEL 2.0 SQLite file.

    The tables are declared exactly as the thesis defines them, constraints
    included, and timestamps are written in the base log's ISO 8601 profile
    (UTC, `+00:00`), so that their text orders as their time (§16).

    Raises:
        SocelWriteError: Rows break a declared constraint (e.g. an interval that
            ends before it starts); nothing is written then.
    """
    with closing(sqlite3.connect(target)) as db:
        table = None
        try:
            with db:
                for table in TABLES:
                    db.execute(f"DROP TABLE IF EXISTS {table.name}")
                    db.execute(table.sqlite_ddl())
                    if has_table(ocel, table.name):
                        _copy_rows(ocel, db, table.name, table.columns)
        except sqlite3.IntegrityError as error:
            raise SocelWriteError(
                f"{table.name if table else 'sOCEL'} breaks a constraint of the sOCEL "
                f"serialization ({error}). validate() shows which rows."
            ) from error


def _copy_rows(ocel: OCEL, db: sqlite3.Connection, table: str, columns: tuple[Column, ...]) -> None:
    present = [column for column in columns if has_column(ocel, table, column.name)]
    values = ", ".join(_write(column) if column in present else "NULL" for column in columns)
    insert = (
        f"INSERT INTO {table} ({', '.join(column.name for column in columns)}) "
        f"VALUES ({', '.join('?' for _ in columns)})"
    )
    cursor = ocel.con.cursor()
    cursor.execute(f"SELECT {values} FROM {ident(table)}")
    while batch := cursor.fetchmany(_BATCH_SIZE):
        db.executemany(insert, batch)


def _read(column: Column) -> str:
    """The SQL reading a text column from SQLite as its declared type."""
    name = ident(column.name)
    if column.type == "TIMESTAMP":
        return utc_timestamp(name)
    if column.type == "REAL":
        return f"TRY_CAST({name} AS DOUBLE)"
    return name


def _write(column: Column) -> str:
    """The SQL giving a column's values as SQLite gets them."""
    name = ident(column.name)
    return _iso_utc(name) if column.type == "TIMESTAMP" else name


def _iso_utc(expr: str) -> str:
    """A UTC timestamp as the base log writes it: seconds, a fraction only when there is one."""
    fraction = f"(epoch_us({expr}) % 1000000)"
    return (
        f"strftime({expr}, '%Y-%m-%dT%H:%M:%S') || CASE "
        f"WHEN {fraction} = 0 THEN '' "
        f"WHEN {fraction} % 1000 = 0 THEN '.' || lpad(({fraction} // 1000)::VARCHAR, 3, '0') "
        f"ELSE '.' || lpad({fraction}::VARCHAR, 6, '0') END || '+00:00'"
    )
