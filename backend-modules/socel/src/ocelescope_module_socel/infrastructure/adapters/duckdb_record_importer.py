import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import get_args

import duckdb
from ocelescope import OCEL
from ocelescope.ocel.constants.pm4py import EID_COL, OID_COL, TIMESTAMP_COL
from ocelescope.ocel.constants.tables import EVENTS_TABLE, OBJECTS_TABLE

from ocelescope_module_socel.domain.exceptions import InvalidRecordFile
from ocelescope_module_socel.domain.models.record_file import (
    ColumnMapping,
    FlowDefinition,
    FlowInFile,
    IssueKind,
    RecordFileColumns,
    RecordFilePreview,
    RecordIssue,
    SampleIssue,
)
from ocelescope_module_socel.infrastructure.schema import (
    EVENT_RECORDS,
    FLOW,
    INTERVAL_RECORDS,
    SOCEL_END_TIME,
)

# What a column of a record file can hold.
ROLES = ("flow", "object", "quantity", "start_time", "end_time", "event")
_EXAMPLES = 5
# The first rows of a file that are shown as they are.
SAMPLE_ROWS = 8

# A number with a decimal comma, with or without dots between the thousands.
_QUANTITY = """
    coalesce(
        TRY_CAST(quantity_text AS DOUBLE),
        CASE WHEN regexp_matches(quantity_text, '^[+-]?[0-9.]*,[0-9]+$')
             THEN TRY_CAST(replace(replace(quantity_text, '.', ''), ',', '.') AS DOUBLE) END
    )
"""


def _time(text: str) -> str:
    """SQL for the time a text gives: ISO with or without offset, kept in UTC,
    or day.month.year as German exports write it."""
    return f"""
        coalesce(
            TRY_CAST(TRY_CAST({text} AS TIMESTAMPTZ) AS TIMESTAMP),
            try_strptime({text}, ['%d.%m.%Y %H:%M:%S', '%d.%m.%Y %H:%M', '%d.%m.%Y'])
        )
    """


# Every row of the file with its values read and what, if anything, keeps it
# out: `issue` is NULL for the rows that can be taken over. Times are kept in
# UTC, as the sOCEL tables hold them.
#
# A row is an interval record (start and end, no event), an event-linked record
# (an event, no start; an end is the event's), or an event's end alone (event
# and end, nothing else): `is_interval`, `is_event_record`, `is_end_only`.
_ROWS = f"""
    WITH read AS (
        SELECT
            line,
            nullif(trim(flow), '') AS flow,
            nullif(trim(object), '') AS object,
            nullif(trim(quantity), '') AS quantity_text,
            nullif(trim(start_time), '') AS start_text,
            nullif(trim(end_time), '') AS end_text,
            nullif(trim(event), '') AS event
        FROM record_file
    ), typed AS (
        SELECT *,
            {_QUANTITY} AS quantity,
            {_time("start_text")} AS start_time,
            {_time("end_text")} AS end_time,
            start_text IS NOT NULL AND end_text IS NOT NULL AND event IS NULL AS is_interval,
            start_text IS NULL AND event IS NOT NULL AS is_event,
            start_text IS NULL AND event IS NOT NULL AND end_text IS NOT NULL
                AND flow IS NULL AND object IS NULL AND quantity_text IS NULL AS is_end_only
        FROM read
    ), placed AS (
        SELECT typed.*, log_event."{EID_COL}" IS NOT NULL AS event_known,
               log_event."{TIMESTAMP_COL}" AS event_time,
               -- the ends given for the event, by the rows that may give one
               min(end_time) FILTER (is_event) OVER (PARTITION BY event) AS first_end,
               max(end_time) FILTER (is_event) OVER (PARTITION BY event) AS last_end
        FROM typed
        LEFT JOIN {EVENTS_TABLE} log_event ON log_event."{EID_COL}" = typed.event
    )
    SELECT *,
        is_event AND NOT is_end_only AS is_event_record,
        CASE
            WHEN NOT is_end_only AND flow IS NULL THEN 'missing_flow'
            WHEN NOT is_end_only AND object IS NULL THEN 'missing_object'
            WHEN NOT is_end_only AND (quantity IS NULL OR NOT isfinite(quantity))
                THEN 'quantity_not_a_number'
            WHEN NOT is_interval AND NOT is_event THEN 'neither_interval_nor_event'
            WHEN end_text IS NOT NULL AND end_time IS NULL THEN 'time_not_readable'
            WHEN is_interval AND start_time IS NULL THEN 'time_not_readable'
            WHEN is_interval AND end_time <= start_time THEN 'end_not_after_start'
            WHEN NOT is_end_only AND object NOT IN (SELECT "{OID_COL}" FROM {OBJECTS_TABLE})
                THEN 'unknown_object'
            WHEN is_event AND NOT event_known THEN 'unknown_event'
            WHEN is_event AND end_time <= event_time THEN 'event_end_not_after_start'
            WHEN is_event AND end_time IS NOT NULL AND first_end <> last_end
                THEN 'conflicting_event_end'
        END AS issue
    FROM placed
"""


class DuckDbRecordImporter:
    """Reads the record file with DuckDB and checks it against the log's own
    database, so that a large file is never walked row by row in Python."""

    def __init__(self, ocel: OCEL) -> None:
        self._ocel = ocel

    def columns(self, content: bytes) -> RecordFileColumns:
        ocel = self._ocel
        cursor = ocel.con.cursor()
        try:
            file, delimiter = _read(cursor, content)
            rows = file.count("*").fetchall()[0][0]
            sample = cursor.execute(f"SELECT * FROM file LIMIT {SAMPLE_ROWS}").fetchall()
            names = file.columns
        except duckdb.Error as error:
            raise InvalidRecordFile(f"The file cannot be read as CSV: {error}") from error
        finally:
            cursor.close()
        return RecordFileColumns(
            columns=tuple(names),
            rows=rows,
            delimiter=delimiter,
            sample=tuple(
                tuple(value.strip() or None if value is not None else None for value in row)
                for row in sample
            ),
        )

    def preview(self, content: bytes, mapping: ColumnMapping) -> RecordFilePreview:
        cursor = _with_record_file(self._ocel, content, mapping)
        try:
            (
                rows,
                usable_rows,
                event_ends,
                records_from,
                records_to,
                decimal_comma,
                day_first_dates,
            ) = cursor.execute(
                f"""
                SELECT count(*), count(*) FILTER (issue IS NULL),
                       count(DISTINCT event) FILTER (issue IS NULL AND is_event
                                                     AND end_time IS NOT NULL),
                       min(start_time) FILTER (issue IS NULL AND is_interval),
                       max(end_time) FILTER (issue IS NULL AND is_interval),
                       coalesce(bool_or(contains(quantity_text, ','))
                                FILTER (issue IS NULL), false),
                       coalesce(bool_or(
                           TRY_CAST(coalesce(start_text, end_text) AS TIMESTAMPTZ) IS NULL
                           AND coalesce(start_time, end_time) IS NOT NULL
                       ) FILTER (issue IS NULL), false)
                FROM ({_ROWS})
                """
            ).fetchall()[0]
            sample_issues = cursor.execute(
                f"""
                SELECT line - 2, issue FROM ({_ROWS})
                WHERE line <= {SAMPLE_ROWS + 1} AND issue IS NOT NULL
                ORDER BY line
                """
            ).fetchall()
            flows = cursor.execute(
                f"""
                SELECT flow, count(*), count(*) FILTER (issue IS NULL),
                       count(*) FILTER (issue IS NULL AND is_interval),
                       count(*) FILTER (issue IS NULL AND is_event_record),
                       count(DISTINCT object) FILTER (issue IS NULL)
                FROM ({_ROWS})
                WHERE flow IS NOT NULL
                GROUP BY 1
                ORDER BY 2 DESC, 1
                """
            ).fetchall()
            issues = cursor.execute(
                f"""
                SELECT issue, count(*),
                       list(DISTINCT CASE issue
                           WHEN 'unknown_object' THEN object
                           WHEN 'unknown_event' THEN event
                           ELSE line::VARCHAR
                       END)[:{_EXAMPLES}]
                FROM ({_ROWS})
                WHERE issue IS NOT NULL
                GROUP BY 1
                ORDER BY 2 DESC, 1
                """
            ).fetchall()
        finally:
            cursor.close()

        kinds: tuple[IssueKind, ...] = get_args(IssueKind)
        return RecordFilePreview(
            rows=rows,
            usable_rows=usable_rows,
            event_ends=event_ends,
            flows=tuple(
                FlowInFile(
                    flow_id=flow_id,
                    rows=count,
                    usable_rows=usable,
                    interval_records=intervals,
                    event_records=events,
                    objects=objects,
                )
                for flow_id, count, usable, intervals, events, objects in flows
            ),
            issues=tuple(
                RecordIssue(kind=kind, rows=count, examples=tuple(examples))
                for kind in kinds
                for issue, count, examples in issues
                if issue == kind
            ),
            records_from=records_from,
            records_to=records_to,
            sample_issues=tuple(SampleIssue(row=row, kind=kind) for row, kind in sample_issues),
            decimal_comma=decimal_comma,
            day_first_dates=day_first_dates,
        )

    def write(
        self,
        content: bytes,
        mapping: ColumnMapping,
        flows: Mapping[str, FlowDefinition],
    ) -> None:
        cursor = _with_record_file(self._ocel, content, mapping)
        try:
            cursor.execute(
                "CREATE TEMP TABLE defined_flow "
                "(flow_id VARCHAR, unit VARCHAR, category VARCHAR, external_ref VARCHAR)"
            )
            if flows:
                cursor.executemany(
                    "INSERT INTO defined_flow VALUES (?, ?, ?, ?)",
                    [
                        (flow_id, flow.unit, flow.category, flow.external_ref)
                        for flow_id, flow in flows.items()
                    ],
                )
            usable = f"""
                SELECT * FROM ({_ROWS})
                WHERE issue IS NULL AND flow IN (SELECT flow_id FROM defined_flow)
            """
            # A flow of the file replaces the log's flow of that name.
            cursor.execute(
                f"""
                DELETE FROM {FLOW.name}
                WHERE flow_id IN (SELECT DISTINCT flow FROM ({usable}))
                """
            )
            cursor.execute(
                f"""
                INSERT INTO {FLOW.name} (flow_id, unit, category, external_ref)
                SELECT flow_id, unit, category, external_ref FROM defined_flow
                WHERE flow_id IN (SELECT DISTINCT flow FROM ({usable}))
                """
            )
            cursor.execute(
                f"""
                INSERT INTO {INTERVAL_RECORDS.name}
                    (record_id, flow_id, object_id, quantity, start_time, end_time)
                SELECT 'ir-' || uuid()::VARCHAR, flow, object, quantity, start_time, end_time
                FROM ({usable}) WHERE is_interval
                """
            )
            cursor.execute(
                f"""
                INSERT INTO {EVENT_RECORDS.name} (record_id, flow_id, object_id, quantity, event_id)
                SELECT 'er-' || uuid()::VARCHAR, flow, object, quantity, event
                FROM ({usable}) WHERE is_event_record
                """
            )
            # An event's end is an attribute of the event; it comes with a record
            # of a defined flow, or on a row of its own.
            cursor.execute(
                f"ALTER TABLE {EVENTS_TABLE} ADD COLUMN IF NOT EXISTS {SOCEL_END_TIME} TIMESTAMP"
            )
            cursor.execute(
                f"""
                UPDATE {EVENTS_TABLE} SET {SOCEL_END_TIME} = given.end_time
                FROM (
                    SELECT event, min(end_time) AS end_time FROM ({_ROWS})
                    WHERE issue IS NULL AND is_event AND end_time IS NOT NULL
                      AND (is_end_only OR flow IN (SELECT flow_id FROM defined_flow))
                    GROUP BY 1
                ) given
                WHERE {EVENTS_TABLE}."{EID_COL}" = given.event
                """
            )
        finally:
            cursor.close()


def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


def _read(cursor: duckdb.DuckDBPyConnection, content: bytes) -> tuple[duckdb.DuckDBPyRelation, str]:
    """The CSV as a relation named `file`, every column as text, and the
    character that separates its columns. DuckDB finds out the delimiter; the
    first line names the columns."""
    if b"\x00" in content:
        raise InvalidRecordFile("The uploaded file is not a text CSV file.")
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "records.csv"
        path.write_bytes(content)
        try:
            (delimiter,) = cursor.execute(
                "SELECT Delimiter FROM sniff_csv(?)", [str(path)]
            ).fetchall()[0]
            table = cursor.read_csv(
                str(path), header=True, all_varchar=True, delimiter=delimiter
            ).to_arrow_table()
        except duckdb.Error as error:
            raise InvalidRecordFile(f"The file cannot be read as CSV: {error}") from error
    cursor.register("file", table)
    return cursor.table("file"), delimiter


def _with_record_file(
    ocel: OCEL, content: bytes, mapping: ColumnMapping
) -> duckdb.DuckDBPyConnection:
    """A cursor on the log's database that also sees the file as `record_file`:
    one text column per role, empty where the file has no column for it, and
    each row's line number in the file."""
    cursor = ocel.con.cursor()
    try:
        file, _ = _read(cursor, content)
        assigned = {role: getattr(mapping, role) for role in ROLES}
        unknown = [name for name in assigned.values() if name and name not in file.columns]
        if unknown:
            raise InvalidRecordFile(f"The file has no column {', '.join(unknown)}.")
        selected = ", ".join(
            f"{_quoted(name)} AS {role}" if name else f"NULL::VARCHAR AS {role}"
            for role, name in assigned.items()
        )
        cursor.execute("SET TimeZone = 'UTC'")
        cursor.execute(
            f"CREATE TEMP TABLE record_file AS "
            f"SELECT row_number() OVER () + 1 AS line, {selected} FROM file"
        )
    except BaseException:
        cursor.close()
        raise
    return cursor


def _has_table(cursor: duckdb.DuckDBPyConnection, table: str) -> bool:
    return bool(
        cursor.execute(
            "SELECT 1 FROM duckdb_tables() WHERE database_name = current_database() "
            "AND schema_name = current_schema() AND table_name = ?",
            [table],
        ).fetchone()
    )
