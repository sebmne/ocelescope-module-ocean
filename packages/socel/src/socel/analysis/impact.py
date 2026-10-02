"""Convert flow quantities into environmental impacts."""

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite
from types import MappingProxyType

from socel.analysis.allocation import (
    AllocationResult,
    CarriedQuantityResult,
    FlowEventQuantity,
)


@dataclass(frozen=True, slots=True)
class ImpactFactors:
    """Impact factor per flow."""

    values: Mapping[str, float]

    def __post_init__(self) -> None:
        normalized: dict[str, float] = {}
        for flow_id, value in self.values.items():
            if not flow_id:
                raise ValueError("Impact-factor flow identifiers must not be empty.")
            if isinstance(value, bool) or not isinstance(value, int | float):
                raise TypeError(f"Impact factor for {flow_id!r} must be numeric.")
            factor = float(value)
            if not isfinite(factor):
                raise ValueError(f"Impact factor for {flow_id!r} must be finite.")
            normalized[flow_id] = factor
        object.__setattr__(self, "values", MappingProxyType(normalized))

    def for_flow(self, flow_id: str) -> float:
        """Return the factor of a flow or fail if none was provided."""
        try:
            return self.values[flow_id]
        except KeyError as error:
            raise ValueError(f"Missing impact factor for flow {flow_id!r}.") from error


@dataclass(frozen=True, slots=True)
class EventImpact:
    """The total impact assigned to one event."""

    event_id: str
    value: float


@dataclass(frozen=True, slots=True)
class EventImpactResult:
    """Impact values for operation events."""

    events: tuple[EventImpact, ...]

    def __post_init__(self) -> None:
        event_ids = [event.event_id for event in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("An event-impact result must contain each event once.")

    @property
    def total(self) -> float:
        return sum(event.value for event in self.events)

    def for_event(self, event_id: str) -> float:
        return next(
            (event.value for event in self.events if event.event_id == event_id),
            0.0,
        )


@dataclass(frozen=True, slots=True)
class HandlingUnitImpact:
    """The total impact assigned to one handling unit."""

    object_id: str
    value: float


@dataclass(frozen=True, slots=True)
class AllocatedImpactResult:
    """Impact allocated directly to handling units."""

    handling_units: tuple[HandlingUnitImpact, ...]
    unallocated: float

    def __post_init__(self) -> None:
        _validate_handling_units(self.handling_units)

    @property
    def allocated(self) -> float:
        return sum(entry.value for entry in self.handling_units)

    def for_handling_unit(self, object_id: str) -> float:
        return _for_handling_unit(self.handling_units, object_id)


@dataclass(frozen=True, slots=True)
class ProductFootprintResult:
    """Lineage-carried partial product footprints."""

    handling_units: tuple[HandlingUnitImpact, ...]
    unallocated: float

    def __post_init__(self) -> None:
        _validate_handling_units(self.handling_units)

    def for_handling_unit(self, object_id: str) -> float:
        return _for_handling_unit(self.handling_units, object_id)


def impact_quantity(
    flow_id: str,
    quantity: float,
    factors: ImpactFactors,
) -> float:
    """Convert a quantity of one flow into an impact value."""
    return factors.for_flow(flow_id) * quantity


def impact_events(
    quantities: tuple[FlowEventQuantity, ...],
    factors: ImpactFactors,
) -> EventImpactResult:
    """Sum converted flow quantities per event."""
    impacts: dict[str, float] = {}
    for quantity in quantities:
        impacts[quantity.event_id] = impacts.get(quantity.event_id, 0.0) + (
            impact_quantity(quantity.flow_id, quantity.quantity, factors)
        )
    return EventImpactResult(
        tuple(
            EventImpact(event_id, value) for event_id, value in sorted(impacts.items())
        )
    )


def impact_allocations(
    allocation: AllocationResult,
    factors: ImpactFactors,
) -> AllocatedImpactResult:
    """Sum converted allocated quantities per handling unit."""
    impacts: dict[str, float] = {}
    unallocated = 0.0
    for flow in allocation.flows:
        factor = factors.for_flow(flow.flow_id)
        unallocated += factor * flow.unallocated
        for quantity in flow.handling_units:
            impacts[quantity.object_id] = (
                impacts.get(quantity.object_id, 0.0) + factor * quantity.quantity
            )
    return AllocatedImpactResult(
        handling_units=tuple(
            HandlingUnitImpact(object_id, value)
            for object_id, value in sorted(impacts.items())
        ),
        unallocated=unallocated,
    )


def product_footprints(
    carried: CarriedQuantityResult,
    factors: ImpactFactors,
) -> ProductFootprintResult:
    """Sum converted carried quantities into partial product footprints."""
    impacts: dict[str, float] = {}
    unallocated = 0.0
    for flow in carried.flows:
        factor = factors.for_flow(flow.flow_id)
        unallocated += factor * flow.unallocated
        for quantity in flow.handling_units:
            impacts[quantity.object_id] = (
                impacts.get(quantity.object_id, 0.0) + factor * quantity.quantity
            )
    return ProductFootprintResult(
        handling_units=tuple(
            HandlingUnitImpact(object_id, value)
            for object_id, value in sorted(impacts.items())
        ),
        unallocated=unallocated,
    )


def _validate_handling_units(entries: tuple[HandlingUnitImpact, ...]) -> None:
    object_ids = [entry.object_id for entry in entries]
    if len(object_ids) != len(set(object_ids)):
        raise ValueError("An impact result must contain each handling unit once.")


def _for_handling_unit(
    entries: tuple[HandlingUnitImpact, ...],
    object_id: str,
) -> float:
    return next(
        (entry.value for entry in entries if entry.object_id == object_id),
        0.0,
    )
