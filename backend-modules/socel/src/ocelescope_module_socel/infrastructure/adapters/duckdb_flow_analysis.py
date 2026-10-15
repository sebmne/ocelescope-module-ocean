from ocelescope.ocel.constants.pm4py import EID_COL, TIMESTAMP_COL
from ocelescope.ocel.constants.tables import EVENTS_TABLE

from ocelescope_module_socel.domain.models.analysis_window import AnalysisWindow
from ocelescope_module_socel.domain.models.flow_quantities import (
    FlowQuantity,
    Period,
    PeriodQuantity,
)
from ocelescope_module_socel.infrastructure.ocelescope_extension import SOCEL
from ocelescope_module_socel.infrastructure.schema import (
    CONTAINED_IN,
    EVENT_RECORDS,
    FLOW,
    INTERVAL_RECORDS,
    SOCEL_END_TIME,
)

# The step from one period to the next, per period.
_STEP: dict[Period, str] = {
    "hour": "INTERVAL 1 HOUR",
    "day": "INTERVAL 1 DAY",
    "week": "INTERVAL 7 DAY",
    "month": "INTERVAL 1 MONTH",
}


class DuckDbFlowAnalysis:
    """Bulk quantities for a request's borrowed sOCEL view.

    Ocelescope owns the source log; this adapter creates no connection of its own.
    Calendar quantification and containment selection stay in bulk SQL.
    """

    def __init__(self, socel: SOCEL) -> None:
        self._socel = socel

    def quantities(self, period: Period) -> tuple[FlowQuantity, ...]:
        socel = self._socel
        counted = _uncovered_instances(socel)
        windows = _calendar_windows(socel, period)
        of_flow: dict[str, list[PeriodQuantity]] = {}
        for flow_id, window_id, inflow, outflow in _window_quantities(socel, windows, counted):
            of_flow.setdefault(flow_id, []).append(
                PeriodQuantity(start=windows[window_id].start, inflow=inflow, outflow=-outflow)
            )
        return tuple(
            FlowQuantity(
                flow_id=flow_id,
                unit=unit,
                inflow=sum(part.inflow for part in of_flow.get(flow_id, [])),
                outflow=sum(part.outflow for part in of_flow.get(flow_id, [])),
                by_period=tuple(of_flow.get(flow_id, [])),
            )
            for flow_id, unit in socel.sql(
                f"SELECT flow_id, unit FROM {FLOW.name} ORDER BY flow_id"
            ).fetchall()
        )


def _uncovered_instances(socel: SOCEL) -> tuple[tuple[str, str], ...]:
    """The flow instances with records that lie inside no instance with records
    of its own: those whose records are not held by an outer one already."""
    rows = socel.sql(
        f"""
        WITH RECURSIVE
        recorded AS (
            SELECT flow_id, object_id FROM {INTERVAL_RECORDS.name}
            UNION SELECT flow_id, object_id FROM {EVENT_RECORDS.name}
        ),
        -- Every instance with each instance it lies inside, directly or further out.
        outward(flow_id, object_id, outer_id, depth) AS (
            SELECT flow_id, object_id, parent_object_id, 1 FROM {CONTAINED_IN.name}
            UNION ALL
            SELECT outward.flow_id, outward.object_id, inside.parent_object_id, depth + 1
            FROM outward JOIN {CONTAINED_IN.name} inside
              ON inside.flow_id = outward.flow_id AND inside.object_id = outward.outer_id
            WHERE depth < 50
        ),
        covered AS (
            SELECT outward.flow_id, outward.object_id
            FROM outward SEMI JOIN recorded
              ON recorded.flow_id = outward.flow_id AND recorded.object_id = outward.outer_id
        )
        SELECT object_id, flow_id FROM recorded ANTI JOIN covered USING (flow_id, object_id)
        """
    ).fetchall()
    return tuple((str(object_id), str(flow_id)) for object_id, flow_id in rows)


def _calendar_windows(socel: SOCEL, period: Period) -> tuple[AnalysisWindow, ...]:
    """The calendar periods (weeks from Monday) from the first record's start to
    the last one's end, as half-open windows."""
    step = _STEP[period]
    event_end = (
        f'event."{SOCEL_END_TIME}"'
        if _has_column(socel, EVENTS_TABLE, SOCEL_END_TIME)
        else "NULL::TIMESTAMP"
    )
    rows = socel.sql(
        f"""
        WITH bound AS (
            SELECT min(start_time) AS first, max(end_time) AS last
            FROM {INTERVAL_RECORDS.name}
            UNION ALL
            SELECT min(event."{TIMESTAMP_COL}"),
                   max(coalesce({event_end}, event."{TIMESTAMP_COL}"))
            FROM {EVENT_RECORDS.name} record
            JOIN {EVENTS_TABLE} event ON event."{EID_COL}" = record.event_id
        ),
        slot AS (
            SELECT unnest(generate_series(
                date_trunc('{period}', min(first)), max(last), {step}
            )) AS start
            FROM bound
        )
        SELECT start, start + {step} FROM slot ORDER BY start
        """
    ).fetchall()
    return tuple(AnalysisWindow(start=start, end=end) for start, end in rows)


def _has_column(socel: SOCEL, table: str, column: str) -> bool:
    return bool(
        socel.sql(
            "SELECT 1 FROM duckdb_columns() WHERE database_name = current_database() "
            "AND schema_name = current_schema() AND table_name = ? AND column_name = ?",
            params=[table, column],
        ).fetchone()
    )


def _window_quantities(
    socel: SOCEL,
    windows: tuple[AnalysisWindow, ...],
    instances: tuple[tuple[str, str], ...],
) -> tuple[tuple[str, int, float, float], ...]:
    """Aggregate signed record shares per flow/window; leave zero-net rows intact."""
    if not windows:
        return ()
    event_end = (
        f'event."{SOCEL_END_TIME}"'
        if _has_column(socel, EVENTS_TABLE, SOCEL_END_TIME)
        else "NULL::TIMESTAMP"
    )
    counted = """
        SELECT * FROM record
        SEMI JOIN (
            SELECT unnest($objects) AS object_id, unnest($flows) AS flow_id
        ) chosen USING (object_id, flow_id)
    """
    parameters = {
        "objects": [object_id for object_id, _ in instances],
        "flows": [flow_id for _, flow_id in instances],
    }
    rows = socel.con.execute(
        f"""
        WITH window_ AS (
            SELECT unnest(range(len($starts))) AS id,
                   unnest($starts)::TIMESTAMP AS a, unnest($ends)::TIMESTAMP AS b
        ),
        -- span(r) (Definition 6.1.1): the interval, or the event's observed
        -- extent; an event-linked record without an end is a point (t is NULL).
        record AS (
            SELECT object_id, flow_id, quantity, start_time AS s, end_time AS t
            FROM {INTERVAL_RECORDS.name}
            UNION ALL
            SELECT record.object_id, record.flow_id, record.quantity,
                   event."{TIMESTAMP_COL}", {event_end}
            FROM {EVENT_RECORDS.name} record
            JOIN {EVENTS_TABLE} event
              ON event."{EID_COL}" = record.event_id
        ),
        counted AS ({counted}),
        -- share(r, w) for every record and window it has a share in.
        part AS (
            SELECT counted.flow_id, window_.id,
                   counted.quantity * epoch(least(t, b) - greatest(s, a)) / epoch(t - s)
                       AS quantity
            FROM counted JOIN window_ ON s < b AND t > a
            WHERE t IS NOT NULL
            UNION ALL
            SELECT counted.flow_id, window_.id, counted.quantity
            FROM counted JOIN window_ ON a <= s AND s < b
            WHERE t IS NULL
        )
        SELECT flow_id, id, coalesce(sum(quantity) FILTER (quantity > 0), 0),
               coalesce(sum(quantity) FILTER (quantity < 0), 0)
        FROM part GROUP BY 1, 2 ORDER BY 1, 2
        """,
        {
            "starts": [window.start for window in windows],
            "ends": [window.end for window in windows],
            **parameters,
        },
    ).fetchall()
    return tuple(
        (str(flow_id), int(window_id), float(inflow), float(outflow))
        for flow_id, window_id, inflow, outflow in rows
    )
