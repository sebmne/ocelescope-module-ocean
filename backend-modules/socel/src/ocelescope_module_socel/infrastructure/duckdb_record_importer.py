import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import get_args

import duckdb
from ocelescope import OCEL
from ocelescope.ocel.constants.pm4py import EID_COL, OID_COL
from ocelescope.ocel.constants.tables import EVENTS_TABLE, OBJECTS_TABLE
from socel.schema import EVENT_RECORDS, FLOW, INTERVAL_RECORDS

from ocelescope_module_socel.domain.exceptions import InvalidRecordFile
from ocelescope_module_socel.domain.models.record_file import (
    FlowDefinition,
    FlowInFile,
    IssueKind,
    RecordFilePreview,
    RecordIssue,
)

COLUMNS = ("flow", "object", "quantity", "start_time", "end_time", "event")
_EXAMPLES = 5

# Every row of the file with its values read and what, if anything, keeps it
# out: `issue` is NULL for the rows that can be taken over. Times are read with
# their offset and kept in UTC, as the sOCEL tables hold them.
_ROWS = f"""
    WITH read AS (
        SELECT
            line,
            nullif(trim(flow), '') AS flow,
            nullif(trim(object), '') AS object,
            TRY_CAST(quantity AS DOUBLE) AS quantity,
            nullif(trim(start_time), '') AS start_text,
            nullif(trim(end_time), '') AS end_text,
            nullif(trim(event), '') AS event
        FROM record_file
    ), typed AS (
        SELECT *,
            TRY_CAST(TRY_CAST(start_text AS TIMESTAMPTZ) AS TIMESTAMP) AS start_time,
            TRY_CAST(TRY_CAST(end_text AS TIMESTAMPTZ) AS TIMESTAMP) AS end_time,
            start_text IS NOT NULL AND end_text IS NOT NULL AND event IS NULL AS is_interval,
            start_text IS NULL AND end_text IS NULL AND event IS NOT NULL AS is_event
        FROM read
    )
    SELECT *,
        CASE
            WHEN flow IS NULL THEN 'missing_flow'
            WHEN object IS NULL THEN 'missing_object'
            WHEN quantity IS NULL OR NOT isfinite(quantity) THEN 'quantity_not_a_number'
            WHEN NOT is_interval AND NOT is_event THEN 'neither_interval_nor_event'
            WHEN is_interval AND (start_time IS NULL OR end_time IS NULL) THEN 'time_not_readable'
            WHEN is_interval AND end_time <= start_time THEN 'end_not_after_start'
            WHEN object NOT IN (SELECT "{OID_COL}" FROM {OBJECTS_TABLE}) THEN 'unknown_object'
            WHEN is_event AND event NOT IN (SELECT "{EID_COL}" FROM {EVENTS_TABLE})
                THEN 'unknown_event'
        END AS issue
    FROM typed
"""


class DuckDbRecordImporter:
    """Reads the record file with DuckDB and checks it against the log's own
    database, so that a large file is never walked row by row in Python."""

    def preview(self, ocel: OCEL, content: bytes) -> RecordFilePreview:
        cursor = _with_record_file(ocel, content)
        try:
            rows, usable_rows, records_from, records_to = cursor.execute(
                f"""
                SELECT count(*), count(*) FILTER (issue IS NULL),
                       min(start_time) FILTER (issue IS NULL AND is_interval),
                       max(end_time) FILTER (issue IS NULL AND is_interval)
                FROM ({_ROWS})
                """
            ).fetchall()[0]
            known = (
                {
                    flow_id: FlowDefinition(unit=unit, category=category)
                    for flow_id, unit, category in cursor.execute(
                        f"SELECT flow_id, unit, category FROM {FLOW.name}"
                    ).fetchall()
                    if unit and category
                }
                if _has_table(cursor, FLOW.name)
                else {}
            )
            flows = cursor.execute(
                f"""
                SELECT flow, count(*), count(*) FILTER (issue IS NULL),
                       count(*) FILTER (issue IS NULL AND is_interval),
                       count(*) FILTER (issue IS NULL AND is_event),
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
            flows=tuple(
                FlowInFile(
                    flow_id=flow_id,
                    rows=count,
                    usable_rows=usable,
                    interval_records=intervals,
                    event_records=events,
                    objects=objects,
                    known=known.get(flow_id),
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
        )

    def write(
        self,
        ocel: OCEL,
        content: bytes,
        flows: Mapping[str, FlowDefinition],
    ) -> None:
        cursor = _with_record_file(ocel, content)
        try:
            cursor.execute(
                "CREATE TEMP TABLE defined_flow (flow_id VARCHAR, unit VARCHAR, category VARCHAR)"
            )
            if flows:
                cursor.executemany(
                    "INSERT INTO defined_flow VALUES (?, ?, ?)",
                    [(flow_id, flow.unit, flow.category) for flow_id, flow in flows.items()],
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
                INSERT INTO {FLOW.name} (flow_id, unit, category)
                SELECT flow_id, unit, category FROM defined_flow
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
                FROM ({usable}) WHERE is_event
                """
            )
        finally:
            cursor.close()


def _with_record_file(ocel: OCEL, content: bytes) -> duckdb.DuckDBPyConnection:
    """A cursor on the log's database that also sees the file as `record_file`:
    its six columns as text, and each row's line number in the file."""
    with tempfile.TemporaryDirectory() as folder:
        path = Path(folder) / "records.csv"
        path.write_bytes(content)
        reader = duckdb.connect()
        try:
            file = reader.read_csv(str(path), header=True, all_varchar=True, delimiter=",")
            names = {name.strip().lower(): name for name in file.columns}
            missing = [column for column in COLUMNS if column not in names]
            if missing:
                raise InvalidRecordFile(
                    f"The file lacks the column(s) {', '.join(missing)}. "
                    f"It needs: {', '.join(COLUMNS)}."
                )
            selected = ", ".join(f'"{names[column]}" AS {column}' for column in COLUMNS)
            table = reader.sql(
                f"SELECT row_number() OVER () + 1 AS line, {selected} FROM file"
            ).to_arrow_table()
        except duckdb.Error as error:
            raise InvalidRecordFile(f"The file cannot be read as CSV: {error}") from error
        finally:
            reader.close()

    cursor = ocel.con.cursor()
    cursor.execute("SET TimeZone = 'UTC'")
    cursor.register("record_file", table)
    return cursor


def _has_table(cursor: duckdb.DuckDBPyConnection, table: str) -> bool:
    return bool(
        cursor.execute(
            "SELECT 1 FROM duckdb_tables() WHERE database_name = current_database() "
            "AND schema_name = current_schema() AND table_name = ?",
            [table],
        ).fetchone()
    )
