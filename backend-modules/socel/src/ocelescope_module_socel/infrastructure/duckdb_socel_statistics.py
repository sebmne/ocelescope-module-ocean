from ocelescope.ocel.constants.pm4py import (
    EID_COL,
    OBJECT_CHANGED_FIELD,
    OID_COL,
    OTYPE_COL,
    TIMESTAMP_COL,
)
from ocelescope.ocel.constants.tables import EVENTS_TABLE, OBJECT_CHANGES_TABLE, OBJECTS_TABLE
from socel import SOCEL
from socel.schema import CONTAINED_IN, EVENT_RECORDS, FLOW, INTERVAL_RECORDS, SOCEL_CLASS

from ocelescope_module_socel.application.ports.socel_statistics import InstanceOrder
from ocelescope_module_socel.domain.models.class_counts import ClassCount, ClassCounts
from ocelescope_module_socel.domain.models.flow_inventory import (
    FlowByObjectType,
    FlowInstancePage,
    FlowInstanceRow,
    FlowSummary,
)
from ocelescope_module_socel.domain.models.socel_status import SocelStatus

# The classes that make an object a handling unit and an event an operation,
# with everything below them in the taxonomy.
_HANDLING_UNIT, _OPERATION = "hu", "op"

# A flow instance is an object at which a flow is observed: through a record, or
# by lying inside or around another instance.
_INSTANCES = f"""
    SELECT flow_id, object_id FROM {INTERVAL_RECORDS.name}
    UNION SELECT flow_id, object_id FROM {EVENT_RECORDS.name}
    UNION SELECT flow_id, object_id FROM {CONTAINED_IN.name}
    UNION SELECT flow_id, parent_object_id FROM {CONTAINED_IN.name}
"""


def _is(column: str, root: str) -> str:
    """SQL for: the class in `column` is `root` or lies below it."""
    return f"({column} = '{root}' OR {column} LIKE '{root}.%')"


class DuckDbSocelStatistics:
    """Counts by aggregate queries on the sOCEL's DuckDB database."""

    def status(self, socel: SOCEL) -> SocelStatus:
        object_class = _object_classes(socel)
        event_class = _event_class(socel)
        row = socel.sql(
            f"""
            SELECT
                (SELECT count(*) FROM {OBJECTS_TABLE}),
                (SELECT count(*) FROM {EVENTS_TABLE}),
                (SELECT count(*) FROM ({object_class}) WHERE {_is("socel_class", _HANDLING_UNIT)}),
                (SELECT count(*) FROM {EVENTS_TABLE} WHERE {_is(event_class, _OPERATION)}),
                (SELECT count(*) FROM {FLOW.name}),
                (SELECT count(*) FROM ({_INSTANCES})),
                (SELECT count(*) FROM {INTERVAL_RECORDS.name}),
                (SELECT count(*) FROM {EVENT_RECORDS.name}),
                (SELECT count(*) FROM {CONTAINED_IN.name}),
                -- Interval records span their interval; event records sit at their event.
                least(
                    (SELECT min(start_time) FROM {INTERVAL_RECORDS.name}),
                    (SELECT min(event."{TIMESTAMP_COL}") FROM {EVENTS_TABLE} event
                     SEMI JOIN {EVENT_RECORDS.name} record ON record.event_id = event."{EID_COL}")
                ),
                greatest(
                    (SELECT max(end_time) FROM {INTERVAL_RECORDS.name}),
                    (SELECT max(event."{TIMESTAMP_COL}") FROM {EVENTS_TABLE} event
                     SEMI JOIN {EVENT_RECORDS.name} record ON record.event_id = event."{EID_COL}")
                )
            """
        ).fetchall()[0]
        return SocelStatus(
            objects=row[0],
            events=row[1],
            handling_units=row[2],
            operations=row[3],
            flows=row[4],
            flow_instances=row[5],
            interval_records=row[6],
            event_records=row[7],
            containments=row[8],
            records_from=row[9],
            records_to=row[10],
        )

    def flows(self, socel: SOCEL) -> tuple[FlowSummary, ...]:
        by_type = socel.sql(
            f"""
            WITH instance AS ({_INSTANCES}),
            per_instance AS (
                SELECT instance.flow_id, object."{OTYPE_COL}" AS object_type,
                       inside.object_id IS NOT NULL AS contained,
                       coalesce(intervals.records, 0) AS interval_records,
                       coalesce(events.records, 0) AS event_records
                FROM instance
                JOIN {OBJECTS_TABLE} object ON object."{OID_COL}" = instance.object_id
                LEFT JOIN {CONTAINED_IN.name} inside USING (flow_id, object_id)
                LEFT JOIN (
                    SELECT flow_id, object_id, count(*) AS records
                    FROM {INTERVAL_RECORDS.name} GROUP BY 1, 2
                ) intervals USING (flow_id, object_id)
                LEFT JOIN (
                    SELECT flow_id, object_id, count(*) AS records
                    FROM {EVENT_RECORDS.name} GROUP BY 1, 2
                ) events USING (flow_id, object_id)
            )
            SELECT flow_id, object_type, count(*), count(*) FILTER (contained),
                   sum(interval_records)::BIGINT, sum(event_records)::BIGINT
            FROM per_instance
            GROUP BY 1, 2
            ORDER BY 1, 3 DESC, 2
            """
        ).fetchall()
        of_flow: dict[str, list[FlowByObjectType]] = {}
        for flow_id, object_type, instances, contained, intervals, events in by_type:
            of_flow.setdefault(flow_id, []).append(
                FlowByObjectType(
                    object_type=object_type,
                    instances=instances,
                    contained=contained,
                    interval_records=intervals,
                    event_records=events,
                )
            )
        return tuple(
            FlowSummary(
                flow_id=flow_id,
                unit=unit,
                category=category,
                external_ref=external_ref,
                instances=sum(part.instances for part in of_flow.get(flow_id, [])),
                contained=sum(part.contained for part in of_flow.get(flow_id, [])),
                interval_records=sum(part.interval_records for part in of_flow.get(flow_id, [])),
                event_records=sum(part.event_records for part in of_flow.get(flow_id, [])),
                by_object_type=tuple(of_flow.get(flow_id, [])),
            )
            for flow_id, unit, category, external_ref in socel.sql(
                f"SELECT flow_id, unit, category, external_ref FROM {FLOW.name} ORDER BY flow_id"
            ).fetchall()
        )

    def flow_instances(
        self,
        socel: SOCEL,
        flow_id: str,
        *,
        object_type: str | None,
        inside: str | None,
        search: str | None,
        order: InstanceOrder,
        offset: int,
        limit: int,
    ) -> FlowInstancePage:
        ordering = "quantity DESC, object_id" if order == "quantity" else "object_id"
        rows = socel.sql(
            f"""
            WITH instance AS (SELECT object_id FROM ({_INSTANCES}) WHERE flow_id = $flow),
            record AS (
                SELECT object_id, count(*) FILTER (is_interval) AS interval_records,
                       count(*) FILTER (NOT is_interval) AS event_records,
                       sum(quantity) AS quantity
                FROM (
                    SELECT object_id, quantity, true AS is_interval
                    FROM {INTERVAL_RECORDS.name} WHERE flow_id = $flow
                    UNION ALL
                    SELECT object_id, quantity, false
                    FROM {EVENT_RECORDS.name} WHERE flow_id = $flow
                )
                GROUP BY 1
            ),
            inside AS (
                SELECT object_id, parent_object_id FROM {CONTAINED_IN.name} WHERE flow_id = $flow
            ),
            around AS (
                SELECT parent_object_id AS object_id, count(*) AS contains FROM inside GROUP BY 1
            )
            SELECT instance.object_id, object."{OTYPE_COL}" AS object_type,
                   inside.parent_object_id, coalesce(around.contains, 0),
                   coalesce(record.interval_records, 0), coalesce(record.event_records, 0),
                   coalesce(record.quantity, 0) AS quantity, count(*) OVER ()
            FROM instance
            JOIN {OBJECTS_TABLE} object ON object."{OID_COL}" = instance.object_id
            LEFT JOIN inside USING (object_id)
            LEFT JOIN around USING (object_id)
            LEFT JOIN record USING (object_id)
            WHERE ($type IS NULL OR object."{OTYPE_COL}" = $type)
              AND ($inside IS NULL OR inside.parent_object_id = $inside)
              AND ($search IS NULL OR contains(lower(instance.object_id), lower($search)))
            ORDER BY {ordering}
            LIMIT $limit OFFSET $offset
            """,
            params={  # pyright: ignore[reportArgumentType]
                "flow": flow_id,
                "type": object_type,
                "inside": inside,
                "search": search,
                "limit": limit,
                "offset": offset,
            },
        ).fetchall()
        return FlowInstancePage(
            total=rows[0][7] if rows else 0,
            rows=tuple(
                FlowInstanceRow(
                    object_id=object_id,
                    object_type=type_,
                    parent_object_id=parent,
                    contains=contains,
                    interval_records=intervals,
                    event_records=events,
                    quantity=quantity,
                )
                for object_id, type_, parent, contains, intervals, events, quantity, _ in rows
            ),
            path=_path_to(socel, flow_id, inside) if inside is not None else (),
        )

    def class_counts(self, socel: SOCEL) -> ClassCounts:
        objects = socel.sql(
            f"""
            SELECT held.socel_class, count(*)
            FROM {OBJECTS_TABLE} object
            LEFT JOIN ({_object_classes(socel)}) held ON held.object_id = object."{OID_COL}"
            GROUP BY 1
            """
        ).fetchall()
        events = socel.sql(
            f"SELECT {_event_class(socel)}, count(*) FROM {EVENTS_TABLE} GROUP BY 1"
        ).fetchall()
        return ClassCounts(
            objects=_class_counts(objects, _HANDLING_UNIT),
            events=_class_counts(events, _OPERATION),
        )


def _path_to(socel: SOCEL, flow_id: str, object_id: str) -> tuple[str, ...]:
    """The objects from the outermost one down to the given one, each lying
    inside the one before, for the flow."""
    rows = socel.sql(
        f"""
        WITH RECURSIVE up(object_id, depth) AS (
            SELECT $object, 0
            UNION ALL
            SELECT inside.parent_object_id, up.depth + 1
            FROM up JOIN {CONTAINED_IN.name} inside
              ON inside.flow_id = $flow AND inside.object_id = up.object_id
            WHERE up.depth < 50
        )
        SELECT object_id FROM up ORDER BY depth DESC
        """,
        params={"flow": flow_id, "object": object_id},  # pyright: ignore[reportArgumentType]
    ).fetchall()
    return tuple(row[0] for row in rows)


def _has_column(socel: SOCEL, table: str, column: str) -> bool:
    return bool(
        socel.sql(
            "SELECT 1 FROM duckdb_columns() WHERE database_name = current_database() "
            "AND schema_name = current_schema() AND table_name = ? AND column_name = ?",
            params=[table, column],
        ).fetchone()
    )


def _event_class(socel: SOCEL) -> str:
    """SQL for an event's class: its column, or nothing when the log has none."""
    return SOCEL_CLASS if _has_column(socel, EVENTS_TABLE, SOCEL_CLASS) else "NULL::VARCHAR"


def _object_classes(socel: SOCEL) -> str:
    """SQL for (object_id, socel_class): the class each classified object holds
    now, which is the latest it was given."""
    if not _has_column(socel, OBJECT_CHANGES_TABLE, SOCEL_CLASS):
        return "SELECT NULL::VARCHAR AS object_id, NULL::VARCHAR AS socel_class WHERE false"
    return f"""
        SELECT "{OID_COL}" AS object_id,
               arg_max({SOCEL_CLASS}, "{TIMESTAMP_COL}") AS socel_class
        FROM {OBJECT_CHANGES_TABLE}
        WHERE "{OBJECT_CHANGED_FIELD}" = '{SOCEL_CLASS}'
        GROUP BY 1
    """


def _class_counts(rows: list[tuple[str | None, int]], core: str) -> tuple[ClassCount, ...]:
    """Counts per class, most frequent first and the unclassified last among
    equals; `core` is the class that, with those below it, makes handling units
    (objects) or operations (events)."""
    ordered = sorted(rows, key=lambda row: (-row[1], row[0] is None, row[0] or ""))
    return tuple(
        ClassCount(
            socel_class=name,
            count=count,
            is_core=name is not None and (name == core or name.startswith(f"{core}.")),
        )
        for name, count in ordered
    )
