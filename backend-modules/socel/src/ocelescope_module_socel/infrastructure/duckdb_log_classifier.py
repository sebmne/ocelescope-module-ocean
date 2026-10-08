import copy
from collections.abc import Mapping

from ocelescope import OCEL
from ocelescope.ocel.constants.pm4py import (
    ACTIVITY_COL,
    OBJECT_CHANGED_FIELD,
    OID_COL,
    OTYPE_COL,
    TIMESTAMP_COL,
)
from ocelescope.ocel.constants.tables import (
    EVENTS_TABLE,
    OBJECT_CHANGES_TABLE,
    OBJECTS_TABLE,
)
from socel.schema import SOCEL_CLASS, TABLES

from ocelescope_module_socel.domain.models.log_classification import (
    LogClassification,
    TypeClassification,
)

# An object's class is an attribute value like any other: a row of the changes
# table. It holds from the start, so it is dated at the epoch.
_SINCE = "TIMESTAMP '1970-01-01 00:00:00'"


class DuckDbLogClassifier:
    """The socel_class of events (a column of the events table) and of objects
    (a field in the object changes), read and written with SQL on the log's
    DuckDB database."""

    def read(self, ocel: OCEL) -> LogClassification:
        event_class = (
            SOCEL_CLASS if _has_column(ocel, EVENTS_TABLE, SOCEL_CLASS) else "NULL::VARCHAR"
        )
        activities = ocel.sql(
            f"""
            SELECT "{ACTIVITY_COL}", count(*), count({event_class}),
                   count(DISTINCT {event_class}), min({event_class})
            FROM {EVENTS_TABLE}
            GROUP BY 1
            ORDER BY 2 DESC, 1
            """
        ).fetchall()
        object_types = ocel.sql(
            f"""
            SELECT o."{OTYPE_COL}", count(*), count(c.socel_class),
                   count(DISTINCT c.socel_class), min(c.socel_class)
            FROM {OBJECTS_TABLE} o
            LEFT JOIN ({_current_object_classes(ocel)}) c USING ("{OID_COL}")
            GROUP BY 1
            ORDER BY 2 DESC, 1
            """
        ).fetchall()
        return LogClassification(
            activities=tuple(_type_classification(row) for row in activities),
            object_types=tuple(_type_classification(row) for row in object_types),
        )

    def classify(
        self,
        ocel: OCEL,
        *,
        activities: Mapping[str, str | None],
        object_types: Mapping[str, str | None],
    ) -> OCEL:
        result = copy.deepcopy(ocel)
        con = result.con
        for table in (EVENTS_TABLE, OBJECT_CHANGES_TABLE):
            con.execute(f"ALTER TABLE {table} ADD COLUMN IF NOT EXISTS {SOCEL_CLASS} VARCHAR")

        for activity, socel_class in activities.items():
            con.execute(
                f'UPDATE {EVENTS_TABLE} SET {SOCEL_CLASS} = ? WHERE "{ACTIVITY_COL}" = ?',
                [socel_class, activity],
            )

        for object_type, socel_class in object_types.items():
            of_type = f'SELECT "{OID_COL}" FROM {OBJECTS_TABLE} WHERE "{OTYPE_COL}" = ?'
            con.execute(
                f"""
                DELETE FROM {OBJECT_CHANGES_TABLE}
                WHERE "{OBJECT_CHANGED_FIELD}" = ? AND "{OID_COL}" IN ({of_type})
                """,
                [SOCEL_CLASS, object_type],
            )
            if socel_class is not None:
                con.execute(
                    f"""
                    INSERT INTO {OBJECT_CHANGES_TABLE}
                        ("{OID_COL}", "{TIMESTAMP_COL}", "{OBJECT_CHANGED_FIELD}", {SOCEL_CLASS})
                    SELECT "{OID_COL}", {_SINCE}, ?, ? FROM ({of_type})
                    """,
                    [SOCEL_CLASS, socel_class, object_type],
                )

        # An sOCEL has its tables even while they are empty.
        for table in TABLES:
            columns = ", ".join(f"{column.name} {column.database_type}" for column in table.columns)
            con.execute(f"CREATE TABLE IF NOT EXISTS {table.name} ({columns})")
        return result


def _has_column(ocel: OCEL, table: str, column: str) -> bool:
    return bool(
        ocel.sql(
            "SELECT 1 FROM duckdb_columns() WHERE database_name = current_database() "
            "AND schema_name = current_schema() AND table_name = ? AND column_name = ?",
            params=[table, column],
        ).fetchone()
    )


def _current_object_classes(ocel: OCEL) -> str:
    """SQL for each object's latest socel_class; no rows when the log has none."""
    if not _has_column(ocel, OBJECT_CHANGES_TABLE, SOCEL_CLASS):
        return f'SELECT NULL::VARCHAR AS "{OID_COL}", NULL::VARCHAR AS socel_class WHERE false'
    return f"""
        SELECT "{OID_COL}", arg_max({SOCEL_CLASS}, "{TIMESTAMP_COL}") AS socel_class
        FROM {OBJECT_CHANGES_TABLE}
        WHERE "{OBJECT_CHANGED_FIELD}" = '{SOCEL_CLASS}'
        GROUP BY 1
    """


def _type_classification(row: tuple) -> TypeClassification:
    name, count, classified, distinct, socel_class = row
    uniform = classified == count and distinct == 1
    return TypeClassification(name=name, count=count, socel_class=socel_class if uniform else None)
