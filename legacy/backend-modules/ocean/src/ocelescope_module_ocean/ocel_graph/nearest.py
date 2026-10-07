from collections.abc import Collection

import polars as pl

from ocelescope_module_ocean.ocel_graph.object_graph import ObjectGraph


def nearest_targets(
    graph: ObjectGraph, targets: Collection[str], max_distance: int | None = None
) -> pl.DataFrame:
    """For every object within reach, its nearest targets - all of them on a tie.

    Returns one row per object and nearest target: object, distance, target.
    Targets are their own nearest target, at distance 0. Objects farther than
    `max_distance`, or not connected to any target, are left out.

    The distances come from one breadth-first search from all targets (rustworkx).
    Graph libraries report only one nearest source per object, so the ties are
    added layer by layer: the nearest targets of an object at distance d are
    those of its neighbours at distance d - 1.
    """
    distances = graph.distances(targets, max_distance)
    if distances.is_empty():
        return pl.DataFrame(schema={"object": pl.String, "distance": pl.Int64, "target": pl.String})

    # Every edge in both directions, kept only where it leads one layer outwards.
    edges = graph.edges()
    both_ways = pl.concat(
        [
            edges.select(pl.col("oid_1").alias("from"), pl.col("oid_2").alias("to")),
            edges.select(pl.col("oid_2").alias("from"), pl.col("oid_1").alias("to")),
        ]
    )
    outwards = (
        both_ways.join(distances.rename({"object": "from", "distance": "d_from"}), on="from")
        .join(distances.rename({"object": "to", "distance": "d_to"}), on="to")
        .filter(pl.col("d_to") == pl.col("d_from") + 1)
    )

    layer = distances.filter(pl.col("distance") == 0).select(
        "object", "distance", pl.col("object").alias("target")
    )
    result = [layer]
    for d in range(1, int(distances["distance"].max()) + 1):  # type: ignore[arg-type]
        layer = (
            outwards.filter(pl.col("d_to") == d)
            .join(layer.select(pl.col("object").alias("from"), "target"), on="from")
            .select(
                pl.col("to").alias("object"), pl.lit(d, dtype=pl.Int64).alias("distance"), "target"
            )
            .unique()
        )
        result.append(layer)
    return pl.concat(result)
