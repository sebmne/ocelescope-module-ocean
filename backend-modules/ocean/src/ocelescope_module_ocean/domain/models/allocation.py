from dataclasses import dataclass
from typing import Literal

import polars as pl

OBJECT_EMISSIONS_KG = "ocean:object_emissions_kg"

# How an event's emissions are distributed to the target objects:
# - ParticipatingTargets: evenly among the targets the event relates to,
# - ClosestTargets: evenly among the nearest targets in the object graph,
# - AllTargets: evenly among all targets.
AllocationRule = Literal["ParticipatingTargets", "ClosestTargets", "AllTargets"]


@dataclass(frozen=True, kw_only=True)
class AllocationConfig:
    target_object_types: tuple[str, ...]
    rule: AllocationRule
    # ClosestTargets only: how the object graph is built and searched.
    pass_via_resources: bool = False
    pass_between_same_type: bool = True
    max_distance: int = 7  # the original OCEAn's default


@dataclass(frozen=True, kw_only=True)
class AllocationSteps:
    """How much each step of an allocation assigned, in kg CO2e."""

    # E2O emissions of the target objects themselves.
    direct_kg: float
    # Split by the chosen allocation rule.
    rule_kg: float
    # The rest, spread over all targets - e.g. events from which no target is reachable.
    fallback_kg: float


# eq=False: the frame cannot be compared with ==, so neither can the object.
@dataclass(frozen=True, kw_only=True, eq=False)
class ObjectEmissions:
    """Emissions allocated to the target objects of an OCEL.

    `per_object` has one row per target object (also those that got nothing):
    ocel:oid, ocel:type, OBJECT_EMISSIONS_KG.
    """

    per_object: pl.DataFrame
    steps: AllocationSteps
    total_kg: float


@dataclass(frozen=True, kw_only=True)
class HistogramBin:
    lower_kg: float
    upper_kg: float
    objects: int


@dataclass(frozen=True, kw_only=True)
class AllocationSummary:
    """What an allocation looks like at a glance: totals and how they spread."""

    total_kg: float
    target_objects: int
    steps: AllocationSteps
    # How many target objects carry how much, in equally wide bins.
    histogram: tuple[HistogramBin, ...]
