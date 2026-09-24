"""Allocating the emissions of events to target objects."""

import math

import polars as pl
from ocelescope import OCEL

from ocelescope_module_ocean.domain.exceptions import (
    AllocationIncompleteError,
    NoTargetObjectsError,
)
from ocelescope_module_ocean.domain.models.allocation import (
    OBJECT_EMISSIONS_KG,
    AllocationConfig,
    AllocationSteps,
    AllocationSummary,
    HistogramBin,
    ObjectEmissions,
)
from ocelescope_module_ocean.domain.models.emissions import EMISSIONS_KG, ProcessEmissions
from ocelescope_module_ocean.ocel_graph import build_object_graph, nearest_targets
from ocelescope_module_ocean.ocel_utils.values import EID, OBJECT_TYPE, OID


def allocate(
    ocel: OCEL,
    emissions: ProcessEmissions,
    config: AllocationConfig,
    *,
    resource_types: frozenset[str] = frozenset(),
) -> ObjectEmissions:
    """Distributes the emissions of events to the target objects, like the
    original OCEAn's allocator, in three steps:

    1. E2O emissions of a target object go to that object.
    2. The rest of each event's emissions is split evenly among the targets the
       configured rule picks for the event.
    3. Whatever no target was picked for is split evenly among all targets.

    Args:
        resource_types: Object types classified as resources; the object graph
            leaves them out unless `config.pass_via_resources`. Until object types
            can be classified, all types are handling units.

    Raises:
        NoTargetObjectsError: The target types have no objects.
    """
    targets = (
        ocel.objects.pl.filter(pl.col(OBJECT_TYPE).is_in(config.target_object_types))
        .select(OID, OBJECT_TYPE)
        .collect()
    )
    if targets.is_empty():
        raise NoTargetObjectsError("The target object types have no objects.")
    target_ids = targets[OID]

    # 1. E2O emissions of targets go directly to them.
    e2o = emissions.e2o_emissions.drop_nulls(EMISSIONS_KG)
    is_target = pl.col(OID).is_in(target_ids.implode())
    direct = e2o.filter(is_target).select(OID, pl.col(EMISSIONS_KG).alias(OBJECT_EMISSIONS_KG))

    # What is left, per event.
    remaining = (
        pl.concat(
            [
                emissions.event_emissions.drop_nulls(EMISSIONS_KG),
                e2o.filter(~is_target).select(EID, EMISSIONS_KG),
            ],
            how="vertical_relaxed",
        )
        .group_by(EID)
        .agg(pl.col(EMISSIONS_KG).sum())
        .filter(pl.col(EMISSIONS_KG) != 0)
    )

    # 2. The rule picks targets per event; the event's share is split evenly among them.
    if config.rule == "AllTargets":
        # Every event picks all targets: the same as splitting the sum.
        by_rule = _spread(targets, float(remaining[EMISSIONS_KG].sum()))
        unallocated = remaining.clear()
    else:
        picked = _pick_targets(ocel, remaining[EID], targets, config, resource_types)
        by_rule = _split_evenly(remaining.join(picked, on=EID, how="inner"))
        unallocated = remaining.join(picked.select(EID).unique(), on=EID, how="anti")

    # 3. Events without picked targets: split among all targets.
    fallback_kg = float(unallocated[EMISSIONS_KG].sum())
    fallback = _spread(targets, fallback_kg)

    per_object = targets.join(
        pl.concat([direct, by_rule, fallback], how="vertical_relaxed")
        .group_by(OID)
        .agg(pl.col(OBJECT_EMISSIONS_KG).sum()),
        on=OID,
        how="left",
    ).with_columns(pl.col(OBJECT_EMISSIONS_KG).fill_null(0.0))

    result = ObjectEmissions(
        per_object=per_object,
        steps=AllocationSteps(
            direct_kg=float(direct[OBJECT_EMISSIONS_KG].sum()),
            rule_kg=float(by_rule[OBJECT_EMISSIONS_KG].sum()),
            fallback_kg=fallback_kg,
        ),
        total_kg=float(per_object[OBJECT_EMISSIONS_KG].sum()),
    )
    if not math.isclose(result.total_kg, emissions.total_kg, rel_tol=1e-6, abs_tol=1e-6):
        raise AllocationIncompleteError(
            f"Allocated {result.total_kg} kg of {emissions.total_kg} kg."
        )
    return result


def _pick_targets(
    ocel: OCEL,
    events: pl.Series,
    targets: pl.DataFrame,
    config: AllocationConfig,
    resource_types: frozenset[str],
) -> pl.DataFrame:
    """The target objects the rule picks per event: ocel:eid, ocel:oid.

    (AllTargets needs no picking; `allocate` spreads its emissions directly.)
    """
    relations = (
        ocel.e2o.pl.select(EID, OID, OBJECT_TYPE)
        .filter(pl.col(EID).is_in(events.implode()))
        .collect()
    )
    if config.rule == "ClosestTargets":
        return _closest_targets(ocel, relations, targets, config, resource_types)
    # ParticipatingTargets
    return relations.filter(pl.col(OID).is_in(targets[OID].implode())).select(EID, OID).unique()


def _closest_targets(
    ocel: OCEL,
    relations: pl.DataFrame,
    targets: pl.DataFrame,
    config: AllocationConfig,
    resource_types: frozenset[str],
) -> pl.DataFrame:
    """Per event, the targets nearest to any of its objects in the object graph.

    The graph holds the handling units (and, with `pass_via_resources`, the
    resources too) plus all targets; emissions never pass from target to target.
    """
    all_types = set(ocel.objects.types)
    graph_types = all_types if config.pass_via_resources else all_types - resource_types
    graph_types |= set(config.target_object_types)
    target_ids = set(targets[OID])

    graph = build_object_graph(
        ocel,
        object_types=graph_types,
        same_type_edges=config.pass_between_same_type,
        no_edges_among=target_ids,
    )
    # Object -> each of its nearest targets, with the distance.
    reach = nearest_targets(graph, target_ids, max_distance=config.max_distance).rename(
        {"target": OID}
    )
    # An event's targets: those of its objects that are closest to a target.
    # First the closest objects per event (one row per object), and only then
    # their targets - joining all objects' targets first explodes on large logs.
    distance = reach.select("object", "distance").unique()
    event_objects = (
        relations.select(EID, pl.col(OID).alias("object"))
        .unique()
        .join(distance, on="object", how="inner")
    )
    closest = event_objects.filter(pl.col("distance") == pl.col("distance").min().over(EID))
    return (
        closest.select(EID, "object")
        .join(reach.select("object", OID), on="object", how="inner")
        .select(EID, OID)
        .unique()
    )


def _spread(targets: pl.DataFrame, kg: float) -> pl.DataFrame:
    """kg split evenly among all targets."""
    return targets.select(OID, pl.lit(kg / targets.height).alias(OBJECT_EMISSIONS_KG))


def _split_evenly(event_targets: pl.DataFrame) -> pl.DataFrame:
    """Each event's emissions split evenly among its targets, summed per target."""
    return (
        event_targets.with_columns(
            (pl.col(EMISSIONS_KG) / pl.len().over(EID)).alias(OBJECT_EMISSIONS_KG)
        )
        .group_by(OID)
        .agg(pl.col(OBJECT_EMISSIONS_KG).sum())
    )


def summarize_allocation(object_emissions: ObjectEmissions) -> AllocationSummary:
    """Totals, steps and the distribution over the target objects."""
    return AllocationSummary(
        total_kg=object_emissions.total_kg,
        target_objects=object_emissions.per_object.height,
        steps=object_emissions.steps,
        histogram=tuple(histogram(object_emissions)),
    )


def histogram(object_emissions: ObjectEmissions, bins: int = 20) -> list[HistogramBin]:
    """How many target objects carry how much, in equally wide bins."""
    values = object_emissions.per_object[OBJECT_EMISSIONS_KG]
    if values.is_empty():
        return []
    low, high = float(values.min()), float(values.max())  # type: ignore[arg-type]
    if low == high:
        return [HistogramBin(lower_kg=low, upper_kg=high, objects=len(values))]
    width = (high - low) / bins
    index = ((values - low) / width).floor().cast(pl.Int64).clip(0, bins - 1)
    per_bin = dict(index.value_counts().rows())
    return [
        HistogramBin(
            lower_kg=low + i * width, upper_kg=low + (i + 1) * width, objects=per_bin.get(i, 0)
        )
        for i in range(bins)
    ]
