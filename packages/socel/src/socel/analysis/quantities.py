from datetime import timedelta

import polars as pl

from socel.analysis._sql import is_top_level, share
from socel.format.records import records_sql
from socel.model.socel import SOCEL


def flow_quantities(
    socel: SOCEL,
    every: timedelta,
    *,
    flow_id: str | None = None,
    top_level: bool = True,
) -> pl.DataFrame:
    """q_fi(w) (Definition 6.1.2) for windows of length `every` over the period
    the records span: flow_id, object_id, window_start, window_end, quantity.
    Windows are aligned to Monday 2000-01-03 00:00 UTC (DuckDB's `time_bucket`),
    so days start at midnight and weeks on Monday, like the calendar weeks of
    Section 7.2.4.

    A record's quantity is spread evenly over its span (Definition 6.1.1); a
    point record counts in the window holding its time. Only windows a record
    reaches are returned, so a missing window is a gap in the data, not a zero.

    Args:
        flow_id: Only this flow's instances.
        top_level: Only flow instances contained in no other, so that summing
            over instances counts every exchange once (Section 7.2.4).
    """
    if every <= timedelta(0):
        raise ValueError("Windows need a positive length.")
    step = f"to_microseconds({int(every / timedelta(microseconds=1))})"
    filters = [is_top_level("r")] if top_level else []
    params: list[object] = []
    if flow_id is not None:
        filters.append("r.flow_id = ?")
        params.append(flow_id)
    where = f"WHERE {' AND '.join(filters)}" if filters else ""

    return socel.sql(
        f"""
        WITH r AS (SELECT * FROM ({records_sql(socel.ocel)}) r {where}),
        bounds AS (
            SELECT time_bucket({step}, min(start_time)) AS lo,
                   max(coalesce(end_time, start_time)) AS hi
            FROM r
        ),
        w AS (
            SELECT t.ws, t.ws + {step} AS we
            FROM bounds, generate_series(bounds.lo, bounds.hi, {step}) AS t(ws)
        )
        SELECT r.flow_id, r.object_id, w.ws AS window_start, w.we AS window_end,
               sum(CASE WHEN r.end_time IS NULL THEN r.quantity
                        ELSE r.quantity * {share("r.start_time", "r.end_time", "w.ws", "w.we")}
                   END) AS quantity
        FROM r JOIN w ON
            (r.end_time IS NULL AND r.start_time >= w.ws AND r.start_time < w.we)
            OR (r.end_time IS NOT NULL AND r.start_time < w.we AND r.end_time > w.ws)
        GROUP BY ALL
        ORDER BY r.flow_id, r.object_id, window_start
        """,
        params,
    ).pl()
