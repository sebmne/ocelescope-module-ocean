from dataclasses import dataclass

import polars as pl

from socel._ocelescope import E2O, EID, OID, ident
from socel.analysis._sql import is_top_level, share
from socel.format.attributes import events_sql
from socel.format.records import records_sql
from socel.format.schema import CONTAINED_IN, EVENT_RECORDS, INTERVAL_RECORDS
from socel.model.socel import SOCEL


@dataclass(frozen=True, eq=False)
class Attribution:
    """The result of time-share attribution (Definition 6.2.1), per flow instance
    with records.

    `by_event`: flow_id, object_id, event_id, quantity - attr_fi(e) > 0.
    `by_instance`: flow_id, object_id, top_level, recorded, attributed, remainder -
    recorded = attributed + remainder (u_fi) for every flow instance.
    """

    by_event: pl.DataFrame
    by_instance: pl.DataFrame


def attribute(socel: SOCEL, *, group_metering: bool = True) -> Attribution:
    """Attributes the records of every flow instance to its eligible operations.

    Event-linked records go to their event if it is eligible; interval records
    are shared, per window between the eligible operations' starts and ends,
    equally among the operations running throughout it (TDABC). An operation
    needs an end time for a share of interval records. What reaches no eligible
    operation is the remainder.

    Eligible are the operations involving the flow instance's object (E_fi). With
    `group_metering`, a flow instance whose contained instances carry no records
    also takes the operations of its directly contained objects (Section 6.2,
    group metering), as a line meter stands for its machines.
    """
    events = events_sql(socel.ocel)
    records = records_sql(socel.ocel)
    iv, er, ci = INTERVAL_RECORDS.name, EVENT_RECORDS.name, CONTAINED_IN.name

    widened = f"""
        UNION
        SELECT fi.flow_id, fi.object_id, o.event_id
        FROM fi
        JOIN {ci} c ON c.flow_id = fi.flow_id AND c.parent_object_id = fi.object_id
        JOIN ops o ON o.object_id = c.object_id
        WHERE NOT EXISTS (
            SELECT 1 FROM {ci} c2 JOIN fi f2
              ON f2.flow_id = c2.flow_id AND f2.object_id = c2.object_id
            WHERE c2.flow_id = fi.flow_id AND c2.parent_object_id = fi.object_id)
    """
    by_event = socel.sql(f"""
        WITH ev AS ({events}),
        fi AS (SELECT DISTINCT flow_id, object_id FROM ({records})),
        ops AS (
            SELECT DISTINCT x.{ident(OID)} AS object_id, ev.event_id
            FROM {E2O} x JOIN ev ON ev.event_id = x.{ident(EID)}
            WHERE ev.is_operation
        ),
        eligible AS (
            SELECT fi.flow_id, fi.object_id, o.event_id
            FROM fi JOIN ops o ON o.object_id = fi.object_id
            {widened if group_metering else ""}
        ),
        d AS (
            SELECT el.flow_id, el.object_id, el.event_id, ev.time AS s, ev.end_time AS t
            FROM eligible el JOIN ev ON ev.event_id = el.event_id
            WHERE ev.end_time IS NOT NULL
        ),
        bp AS (
            SELECT flow_id, object_id, s AS p FROM d
            UNION SELECT flow_id, object_id, t FROM d
        ),
        win AS (
            SELECT * FROM (
                SELECT flow_id, object_id, p AS a,
                       lead(p) OVER (PARTITION BY flow_id, object_id ORDER BY p) AS b
                FROM bp)
            WHERE b IS NOT NULL
        ),
        active AS (
            SELECT w.flow_id, w.object_id, w.a, d.event_id,
                   count(*) OVER (PARTITION BY w.flow_id, w.object_id, w.a) AS n
            FROM win w JOIN d
              ON d.flow_id = w.flow_id AND d.object_id = w.object_id
             AND d.s <= w.a AND w.b <= d.t
        ),
        window_share AS (
            SELECT w.flow_id, w.object_id, w.a,
                   sum(i.quantity * {share("i.start_time", "i.end_time", "w.a", "w.b")}) AS q
            FROM win w JOIN {iv} i
              ON i.flow_id = w.flow_id AND i.object_id = w.object_id
             AND i.start_time < w.b AND i.end_time > w.a
            GROUP BY ALL
        ),
        shares AS (
            SELECT a.flow_id, a.object_id, a.event_id, s.q / a.n AS q
            FROM active a JOIN window_share s USING (flow_id, object_id, a)
            UNION ALL
            SELECT r.flow_id, r.object_id, r.event_id, r.quantity
            FROM {er} r JOIN eligible el USING (flow_id, object_id, event_id)
        )
        SELECT flow_id, object_id, event_id, sum(q) AS quantity
        FROM shares GROUP BY ALL HAVING sum(q) <> 0
        ORDER BY flow_id, object_id, event_id
    """).pl()

    recorded = socel.sql(f"""
        SELECT r.flow_id, r.object_id, {is_top_level("r")} AS top_level,
               sum(r.quantity) AS recorded
        FROM ({records}) r GROUP BY ALL
    """).pl()
    attributed = by_event.group_by("flow_id", "object_id").agg(
        pl.col("quantity").sum().alias("attributed")
    )
    by_instance = (
        recorded.join(attributed, on=["flow_id", "object_id"], how="left")
        .with_columns(pl.col("attributed").fill_null(0.0))
        .with_columns((pl.col("recorded") - pl.col("attributed")).alias("remainder"))
        .sort("flow_id", "object_id")
    )
    return Attribution(by_event=by_event, by_instance=by_instance)
