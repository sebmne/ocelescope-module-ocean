from collections.abc import Collection, Iterator

import polars as pl
import rustworkx as rx
from ocelescope import OCEL

_OID, _TYPE, _EID = "ocel:oid", "ocel:type", "ocel:eid"


class ObjectGraph:
    """Undirected graph of objects, identified by their object ids.

    Backed by rustworkx, whose nodes are integer indices; the object ids are
    mapped to and from them here, so callers never see the indices.
    """

    def __init__(self, objects: pl.Series, edges: pl.DataFrame) -> None:
        """objects: the object ids; edges: columns oid_1, oid_2 (both objects included)."""
        self._ids = objects.rename("oid")
        self._index = {oid: i for i, oid in enumerate(self._ids)}
        index = pl.DataFrame({"oid": self._ids, "i": pl.int_range(len(self._ids), eager=True)})
        self._edges = (
            edges.join(index.rename({"oid": "oid_1", "i": "i_1"}), on="oid_1")
            .join(index.rename({"oid": "oid_2", "i": "i_2"}), on="oid_2")
            .select("oid_1", "oid_2", "i_1", "i_2")
        )
        self._graph = rx.PyGraph(multigraph=False)
        self._graph.add_nodes_from(range(len(self._ids)))
        self._graph.extend_from_edge_list(self._edges.select("i_1", "i_2").rows())

    def __contains__(self, oid: object) -> bool:
        return oid in self._index

    def __len__(self) -> int:
        """Number of objects."""
        return len(self._ids)

    @property
    def number_of_edges(self) -> int:
        return self._graph.num_edges()

    def neighbors(self, oid: str) -> Iterator[str]:
        """The objects directly connected to `oid`."""
        return (self._ids[i] for i in self._graph.neighbors(self._index[oid]))

    def edges(self) -> pl.DataFrame:
        """Every edge once: oid_1, oid_2."""
        return self._edges.select("oid_1", "oid_2")

    def distances(self, sources: Collection[str], max_distance: int | None = None) -> pl.DataFrame:
        """How far each object is from the nearest source: object, distance.

        A breadth-first search from all sources at once, run by rustworkx. Objects
        farther than `max_distance`, or not connected to a source, are left out.
        """
        start = [self._index[oid] for oid in sources if oid in self._index]
        if not start:
            return pl.DataFrame(schema={"object": pl.String, "distance": pl.Int64})
        layers = rx.bfs_layers(self._graph, start)
        if max_distance is not None:
            layers = layers[: max_distance + 1]
        return pl.DataFrame(
            {
                "object": self._ids.gather([i for layer in layers for i in layer]),
                "distance": [d for d, layer in enumerate(layers) for _ in layer],
            },
            schema={"object": pl.String, "distance": pl.Int64},
        )


def build_object_graph(
    ocel: OCEL,
    *,
    object_types: Collection[str] | None = None,
    include_o2o: bool = True,
    same_type_edges: bool = True,
    no_edges_among: Collection[str] = (),
) -> ObjectGraph:
    """The undirected graph of how an OCEL's objects relate.

    Nodes are objects (every object of the types, including unrelated ones).
    Two objects are connected when they take part in a common event, or, with
    `include_o2o`, when an O2O relation links them in either direction.

    Args:
        object_types: Objects of these types only; None means all.
        include_o2o: Also connect objects related by O2O relations.
        same_type_edges: Keep edges between two objects of the same type.
        no_edges_among: No edge between any two of these objects, e.g. so that
            something spreading through the graph does not pass from one to another.
    """
    types = set(object_types) if object_types is not None else None

    objects = ocel.objects.pl.select(_OID, _TYPE)
    if types is not None:
        objects = objects.filter(pl.col(_TYPE).is_in(types))
    nodes = objects.collect()

    edges = [_shared_event_edges(ocel, types)]
    if include_o2o:
        edges.append(_o2o_edges(ocel, types))
    pairs = pl.concat(edges).unique()

    if not same_type_edges:
        pairs = pairs.filter(pl.col("type_1") != pl.col("type_2"))
    if no_edges_among:
        among = list(no_edges_among)
        pairs = pairs.filter(~(pl.col("oid_1").is_in(among) & pl.col("oid_2").is_in(among)))

    return ObjectGraph(objects=nodes[_OID], edges=pairs.select("oid_1", "oid_2"))


def _shared_event_edges(ocel: OCEL, types: set[str] | None) -> pl.DataFrame:
    """Every pair of objects taking part in a common event, smaller id first."""
    relations = ocel.e2o.pl.select(_EID, _OID, _TYPE)
    if types is not None:
        relations = relations.filter(pl.col(_TYPE).is_in(types))
    relations = relations.unique().collect()
    return _ordered(
        relations.join(relations, on=_EID, suffix="_2").select(
            pl.col(_OID).alias("a"),
            pl.col(_TYPE).alias("type_a"),
            pl.col(f"{_OID}_2").alias("b"),
            pl.col(f"{_TYPE}_2").alias("type_b"),
        )
    )


def _o2o_edges(ocel: OCEL, types: set[str] | None) -> pl.DataFrame:
    """Every pair of objects linked by an O2O relation, smaller id first."""
    relations = ocel.o2o.typed_pl
    if types is not None:
        relations = relations.filter(
            pl.col("ocel:type_1").is_in(types) & pl.col("ocel:type_2").is_in(types)
        )
    return _ordered(
        relations.select(
            pl.col("ocel:oid_1").alias("a"),
            pl.col("ocel:type_1").alias("type_a"),
            pl.col("ocel:oid_2").alias("b"),
            pl.col("ocel:type_2").alias("type_b"),
        ).collect()
    )


def _ordered(pairs: pl.DataFrame) -> pl.DataFrame:
    """Undirected pairs without self-loops: oid_1 < oid_2."""
    first = pl.col("a") < pl.col("b")
    return pairs.filter(pl.col("a") != pl.col("b")).select(
        pl.when(first).then(pl.col("a")).otherwise(pl.col("b")).alias("oid_1"),
        pl.when(first).then(pl.col("type_a")).otherwise(pl.col("type_b")).alias("type_1"),
        pl.when(first).then(pl.col("b")).otherwise(pl.col("a")).alias("oid_2"),
        pl.when(first).then(pl.col("type_b")).otherwise(pl.col("type_a")).alias("type_2"),
    )
