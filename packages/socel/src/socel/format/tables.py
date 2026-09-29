"""The four sOCEL tables in an OCEL's DuckDB database: creating, filling, pruning."""

from ocelescope import OCEL
from polars import DataFrame

from socel._ocelescope import has_table, ident, reference_target
from socel.errors import NotAnSocelError
from socel.format.schema import DUCKDB_TYPES, TABLES, Table


def create_missing_tables(ocel: OCEL) -> None:
    """Adds the sOCEL tables the OCEL lacks, empty."""
    for table in TABLES:
        if not has_table(ocel, table.name):
            ocel.con.execute(table.duckdb_ddl())


def require_table(ocel: OCEL, table: Table) -> None:
    if not has_table(ocel, table.name):
        raise NotAnSocelError(f"This log has no {table.name} table: it is no sOCEL.")


def append_rows(ocel: OCEL, table: Table, rows: DataFrame) -> None:
    """Appends rows to a table, cast to its column types.

    Columns are matched by name; nullable columns may be left out. Whether the rows
    make a valid sOCEL is for the validation to say.

    Raises:
        ValueError: Unknown columns, or required ones missing.
    """
    require_table(ocel, table)
    unknown = sorted(set(rows.columns) - set(table.column_names))
    missing = sorted(set(table.required_columns) - set(rows.columns))
    if unknown or missing:
        raise ValueError(
            f"Rows for {table.name} do not fit its columns: "
            f"unknown {unknown or 'none'}, missing {missing or 'none'}."
        )
    view = f"_socel_new_{table.name}"
    values = ", ".join(
        f"CAST({ident(column.name)} AS {DUCKDB_TYPES[column.type]})"
        if column.name in rows.columns
        else "NULL"
        for column in table.columns
    )
    ocel.con.register(view, rows)
    try:
        ocel.con.execute(f"INSERT INTO {ident(table.name)} SELECT {values} FROM {ident(view)}")
    finally:
        ocel.con.unregister(view)


def drop_dangling_references(ocel: OCEL) -> None:
    """Removes rows referencing an object or event the log no longer has - after a
    filter took them. Flows stay, even without records."""
    for table in TABLES:
        if not has_table(ocel, table.name):
            continue
        for key in table.foreign_keys:
            if key.references_table not in ("object", "event"):
                continue
            target_table, target_column = reference_target(
                key.references_table, key.references_column
            )
            ocel.con.execute(
                f"DELETE FROM {ident(table.name)} WHERE {ident(key.column)} NOT IN "
                f"(SELECT {ident(target_column)} FROM {ident(target_table)})"
            )
