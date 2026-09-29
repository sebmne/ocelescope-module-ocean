from collections.abc import Mapping, Sequence

import polars as pl


def impact(
    quantities: pl.DataFrame, factors: Mapping[str, float], by: Sequence[str]
) -> pl.DataFrame:
    """impact_f(q) = cf(f)·q summed over the flows (Definition 6.4.1): the frame's
    quantities, per flow_id, in impact units, e.g. kg CO2e.

    Works on any of the analysis' frames: attr^G_f(e) per event gives impact^G(e),
    alloc^G_f(h) per unit impact^G(h), carr^G_f(h) the partial footprint pf^G(h).
    Flows without a factor are left out - no factor, no impact (Table 7.2).

    Args:
        quantities: flow_id, quantity, and the columns `by`.
        factors: flow_id -> impact per unit of the flow.
        by: The columns to sum per, e.g. ["event_id"]; [] for the total.

    Returns:
        The columns `by`, and impact.
    """
    table = pl.DataFrame(
        {"flow_id": list(factors), "factor": list(factors.values())},
        schema={"flow_id": pl.String, "factor": pl.Float64},
    )
    weighted = quantities.join(table, on="flow_id").with_columns(
        (pl.col("quantity") * pl.col("factor")).alias("impact")
    )
    if not by:
        return weighted.select(pl.col("impact").sum())
    return weighted.group_by(*by).agg(pl.col("impact").sum()).sort(*by)
