from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class UnitAllocation:
    """What a handling unit was allocated of a flow and, with a lineage, what it
    carries including its share of its ancestors'. `is_end_unit`: it has no
    children, so what it carries is final."""

    object_id: str
    object_type: str
    allocated: float
    carried: float | None
    is_end_unit: bool


@dataclass(frozen=True, kw_only=True)
class FlowAllocation:
    """A flow allocated to the handling units of the operations it was attributed
    to: recorded = allocated + unallocated. `units`: the largest shares - with a
    lineage, the end units' carried quantities - and `unit_count` how many there
    are."""

    flow_id: str
    unit: str
    recorded: float
    attributed: float
    allocated: float
    unallocated: float
    units: tuple[UnitAllocation, ...]
    unit_count: int


@dataclass(frozen=True, kw_only=True)
class AllocationOverview:
    """Every flow's allocation. `has_lineage`: carried quantities are included;
    `lineage_problem`: why not, if the chosen lineage settings do not work."""

    flows: tuple[FlowAllocation, ...]
    has_lineage: bool
    lineage_problem: str | None
