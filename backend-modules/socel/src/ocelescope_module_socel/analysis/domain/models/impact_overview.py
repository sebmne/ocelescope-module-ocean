from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class FlowImpact:
    """A flow's impact in kg CO2e: of all it recorded, of what reached
    operations, and of what reached handling units."""

    flow_id: str
    unit: str
    impact_per_unit: float
    recorded: float
    attributed: float
    allocated: float


@dataclass(frozen=True, kw_only=True)
class ActivityImpact:
    """The impact of an activity's operations, in kg CO2e."""

    activity: str
    impact: float
    operations: int


@dataclass(frozen=True, kw_only=True)
class EndUnitFootprint:
    """What an end unit carries in kg CO2e, and per kg of its mass."""

    object_id: str
    object_type: str
    footprint: float
    mass: float | None
    footprint_per_kg: float | None


@dataclass(frozen=True, kw_only=True)
class FootprintBin:
    """How many end units have a footprint per kg in [lower, upper)."""

    lower: float
    upper: float
    end_units: int


@dataclass(frozen=True, kw_only=True)
class ImpactOverview:
    """The recorded flows in kg CO2e, with the emission factors set: per flow,
    per activity, and per end unit. `end_units`: those with the largest
    footprint per kg; they need a lineage."""

    recorded: float
    attributed: float
    allocated: float
    flows: tuple[FlowImpact, ...]
    activities: tuple[ActivityImpact, ...]
    end_units: tuple[EndUnitFootprint, ...]
    end_unit_count: int
    median_footprint_per_kg: float | None
    footprint_bins: tuple[FootprintBin, ...]
    lineage_problem: str | None
