from dataclasses import dataclass

import polars as pl

from socel._ocelescope import E2O, EID, OID, ident
from socel.analysis.attribution import Attribution
from socel.format.attributes import objects_sql
from socel.model.socel import SOCEL


@dataclass(frozen=True, eq=False)
class Allocation:
    """The result of allocating attributed quantities to handling units
    (Definitions 6.3.1 and 6.3.2), over the analyzed flow instances G.

    `by_event`: flow_id, event_id, quantity - attr^G_f(e).
    `by_unit`: flow_id, object_id, quantity - alloc^G_f(h), for units that got some.
    `by_flow`: flow_id, recorded, attributed, allocated, unallocated - recorded is
    what G's records hold; unallocated (u^G_f) = recorded - allocated.
    """

    by_event: pl.DataFrame
    by_unit: pl.DataFrame
    by_flow: pl.DataFrame


def allocate(socel: SOCEL, attribution: Attribution) -> Allocation:
    """Divides each event's attributed quantity equally among the handling units
    it involves, tg(e) = obj(e) ∩ HU (Definition 6.3.2). G is the set of flow
    instances contained in no other, as in the attribution's `top_level`.

    Quantities of events without a handling unit stay unallocated, unlike Graves
    et al.'s ParticipatingTargets, which spreads them over all targets.
    """
    counted = attribution.by_instance.filter(pl.col("top_level"))
    by_event = (
        attribution.by_event.join(
            counted.select("flow_id", "object_id"), on=["flow_id", "object_id"]
        )
        .group_by("flow_id", "event_id")
        .agg(pl.col("quantity").sum())
        .sort("flow_id", "event_id")
    )
    targets = socel.sql(f"""
        SELECT DISTINCT x.{ident(EID)} AS event_id, x.{ident(OID)} AS object_id
        FROM {E2O} x JOIN ({objects_sql(socel.ocel)}) o ON o.object_id = x.{ident(OID)}
        WHERE o.is_handling_unit
    """).pl()
    shares = targets.join(targets.group_by("event_id").agg(pl.len().alias("units")), on="event_id")
    by_unit = (
        by_event.join(shares, on="event_id")
        .group_by("flow_id", "object_id")
        .agg((pl.col("quantity") / pl.col("units")).sum().alias("quantity"))
        .sort("flow_id", "object_id")
    )

    by_flow = (
        counted.group_by("flow_id")
        .agg(pl.col("recorded").sum(), pl.col("attributed").sum())
        .join(
            by_unit.group_by("flow_id").agg(pl.col("quantity").sum().alias("allocated")),
            on="flow_id",
            how="left",
        )
        .with_columns(pl.col("allocated").fill_null(0.0))
        .with_columns((pl.col("recorded") - pl.col("allocated")).alias("unallocated"))
        .sort("flow_id")
    )
    return Allocation(by_event=by_event, by_unit=by_unit, by_flow=by_flow)
