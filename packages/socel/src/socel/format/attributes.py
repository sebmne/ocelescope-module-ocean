"""The reserved attributes (Section 5.5, Appendix A.1): `socel_class` of objects and
events, `socel_end_time` of events - how they are stored, read and written.

They are ordinary OCEL attributes, optional per type. Ocelescope holds object
attributes as rows of `object_changes`; an object's `socel_class` is its initial
value, the row at 1970-01-01, which Ocelescope reads and writes as the OCEL 2.0
initial row. Later rows are ignored for it. Event attributes are columns of
`events`.

Everything here is SQL over the OCEL's database, so the model and the
validation share one reading of the attributes.
"""

import polars as pl
from ocelescope import OCEL

from socel._ocelescope import (
    ACTIVITY,
    EID,
    EPOCH,
    EVENTS,
    FIELD,
    OBJECT_CHANGES,
    OBJECT_TYPE,
    OBJECTS,
    OID,
    TIME,
    has_column,
    ident,
)
from socel.format.schema import HANDLING_UNIT, OPERATION, SOCEL_CLASS, SOCEL_END_TIME

# ---- Reading -----------------------------------------------------------------


def objects_sql(ocel: OCEL) -> str:
    """Every object: object_id, object_type, socel_class (its initial value, or
    null), is_handling_unit (its class' first segment is `hu`)."""
    if has_column(ocel, OBJECT_CHANGES, SOCEL_CLASS):
        classes = f"""
            SELECT {ident(OID)} AS object_id, any_value({SOCEL_CLASS}) AS socel_class
            FROM {OBJECT_CHANGES}
            WHERE {ident(FIELD)} = '{SOCEL_CLASS}'
              AND {ident(TIME)} = TIMESTAMP '{EPOCH.isoformat(sep=" ")}'
            GROUP BY {ident(OID)}
        """
    else:
        classes = "SELECT NULL::VARCHAR AS object_id, NULL::VARCHAR AS socel_class LIMIT 0"
    return f"""
        SELECT o.{ident(OID)} AS object_id, o.{ident(OBJECT_TYPE)} AS object_type,
               c.socel_class, {_first_segment("c.socel_class", HANDLING_UNIT)} AS is_handling_unit
        FROM {OBJECTS} o LEFT JOIN ({classes}) c ON c.object_id = o.{ident(OID)}
    """


def events_sql(ocel: OCEL) -> str:
    """Every event: event_id, activity, time, end_time (null for a point),
    socel_class, is_operation (its class' first segment is `op`)."""
    socel_class = _event_column(ocel, SOCEL_CLASS, "VARCHAR")
    end_time = _event_column(ocel, SOCEL_END_TIME, "TIMESTAMP")
    return f"""
        SELECT {ident(EID)} AS event_id, {ident(ACTIVITY)} AS activity, {ident(TIME)} AS time,
               {end_time} AS end_time, {socel_class} AS socel_class,
               {_first_segment(socel_class, OPERATION)} AS is_operation
        FROM {EVENTS}
    """


def _first_segment(expression: str, segment: str) -> str:
    """Whether a class' first segment - before the first period, or all of it - is
    `segment`; false for a null class (Section 5.5)."""
    return f"coalesce(split_part({expression}, '.', 1) = '{segment}', false)"


def _event_column(ocel: OCEL, name: str, duckdb_type: str) -> str:
    """The attribute as a typed expression, or NULL where the log lacks it."""
    if has_column(ocel, EVENTS, name):
        return f"TRY_CAST({ident(name)} AS {duckdb_type})"
    return f"NULL::{duckdb_type}"


# ---- Writing -----------------------------------------------------------------


def write_object_classes(ocel: OCEL, classes: pl.DataFrame) -> None:
    """Sets objects' `socel_class` (columns object_id, socel_class; null clears it)
    as their initial value, replacing any initial class they had."""
    con = ocel.con
    if not has_column(ocel, OBJECT_CHANGES, SOCEL_CLASS):
        con.execute(f"ALTER TABLE {OBJECT_CHANGES} ADD COLUMN {SOCEL_CLASS} VARCHAR")
    con.register("_socel_classes", classes)
    try:
        con.execute(
            f"""DELETE FROM {OBJECT_CHANGES}
                WHERE {ident(FIELD)} = ? AND {ident(TIME)} = ?
                  AND {ident(OID)} IN (SELECT object_id FROM _socel_classes)""",
            [SOCEL_CLASS, EPOCH],
        )
        con.execute(
            f"""INSERT INTO {OBJECT_CHANGES}
                    ({ident(OID)}, {ident(TIME)}, {ident(FIELD)}, {SOCEL_CLASS})
                SELECT object_id, ?, ?, socel_class FROM _socel_classes
                WHERE socel_class IS NOT NULL""",
            [EPOCH, SOCEL_CLASS],
        )
    finally:
        con.unregister("_socel_classes")


def write_event_values(ocel: OCEL, column: str, duckdb_type: str, values: pl.DataFrame) -> None:
    """Sets an event attribute (columns event_id, value; null clears it)."""
    con = ocel.con
    if not has_column(ocel, EVENTS, column):
        con.execute(f"ALTER TABLE {EVENTS} ADD COLUMN {column} {duckdb_type}")
    con.register("_socel_values", values)
    try:
        con.execute(f"""
            UPDATE {EVENTS} SET {column} = v.value
            FROM _socel_values v WHERE {EVENTS}.{ident(EID)} = v.event_id
        """)
    finally:
        con.unregister("_socel_values")
