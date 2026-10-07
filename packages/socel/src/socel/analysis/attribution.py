"""Time-share attribution."""

from dataclasses import dataclass
from datetime import datetime
from itertools import pairwise
from math import isclose

from socel.analysis.quantification import AnalysisWindow, _event_span, share
from socel.domain import EventRecord, FlowInstance, IntervalRecord
from socel.socel import SOCEL


@dataclass(frozen=True, slots=True)
class AttributionScope:
    """The flow instance and optional operation set used for attribution."""

    flow_instance: FlowInstance
    eligible_operations: frozenset[str] | None = None
    include_contained_operations: bool = False

    def __post_init__(self) -> None:
        if self.eligible_operations is not None and any(
            not event_id for event_id in self.eligible_operations
        ):
            raise ValueError("Eligible operation identifiers must not be empty.")
        if self.eligible_operations is not None and self.include_contained_operations:
            raise ValueError(
                "Explicit eligible operations cannot be combined with contained "
                "operations."
            )


@dataclass(frozen=True, slots=True)
class EventAttribution:
    """The quantity attributed to one eligible operation."""

    event_id: str
    quantity: float


@dataclass(frozen=True, slots=True)
class AttributionResult:
    """Attributed event quantities and their unreconciled remainder."""

    events: tuple[EventAttribution, ...]
    unattributed: float
    recorded: float

    def __post_init__(self) -> None:
        event_ids = [event.event_id for event in self.events]
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("An attribution result must contain each event once.")
        if not isclose(
            self.attributed + self.unattributed,
            self.recorded,
            rel_tol=1e-12,
            abs_tol=1e-12,
        ):
            raise ValueError("Attributed and unattributed quantities must reconcile.")

    @property
    def attributed(self) -> float:
        """The quantity assigned to eligible operations."""
        return sum(event.quantity for event in self.events)

    def for_event(self, event_id: str) -> float:
        """Return the attributed quantity of an event, or zero if absent."""
        return next(
            (event.quantity for event in self.events if event.event_id == event_id),
            0.0,
        )


def attribute(socel: SOCEL, scope: AttributionScope) -> AttributionResult:
    """Attribute the records of one flow instance to eligible operations."""
    records = socel.measurements.for_instance(scope.flow_instance)
    eligible = (
        scope.eligible_operations
        if scope.eligible_operations is not None
        else _default_eligible_operations(
            socel,
            scope.flow_instance,
            scope.include_contained_operations,
        )
    )
    quantities = {event_id: 0.0 for event_id in sorted(eligible)}

    for record in records:
        if isinstance(record, EventRecord) and record.event_id in quantities:
            quantities[record.event_id] += record.quantity

    intervals = tuple(
        record for record in records if isinstance(record, IntervalRecord)
    )
    spans = _duration_spans(socel, eligible)
    for window in _windows(spans):
        active = tuple(
            event_id
            for event_id, (start, end) in spans.items()
            if start <= window.start and window.end <= end
        )
        if not active:
            continue

        window_quantity = sum(
            (share(socel, record, window) for record in intervals),
            start=0.0,
        )
        event_share = window_quantity / len(active)
        for event_id in active:
            quantities[event_id] += event_share

    recorded = sum((record.quantity for record in records), start=0.0)
    attributed = sum(quantities.values())
    return AttributionResult(
        events=tuple(
            EventAttribution(event_id, event_quantity)
            for event_id, event_quantity in quantities.items()
        ),
        unattributed=recorded - attributed,
        recorded=recorded,
    )


def _default_eligible_operations(
    socel: SOCEL,
    instance: FlowInstance,
    include_contained: bool,
) -> frozenset[str]:
    object_ids = {instance.object_id}
    if include_contained:
        object_ids.update(
            child.object_id for child in socel.flow_instances.children(instance)
        )
    return frozenset(
        event_id
        for object_id in object_ids
        for event_id in _operations_for_object(socel, object_id)
    )


def _operations_for_object(socel: SOCEL, object_id: str) -> tuple[str, ...]:
    event_ids = (
        str(event_id) for event_id in socel.e2o.get_events_of_object(object_id)
    )
    return tuple(
        event_id
        for event_id in event_ids
        if (class_name := socel.classifications.event_class(event_id)) is not None
        and socel.taxonomies.event_classes.is_a(class_name, "op")
    )


def _duration_spans(
    socel: SOCEL,
    event_ids: frozenset[str],
) -> dict[str, tuple[datetime, datetime]]:
    spans: dict[str, tuple[datetime, datetime]] = {}
    for event_id in event_ids:
        start, end = _event_span(socel, event_id)
        if end is not None:
            spans[event_id] = (start, end)
    return spans


def _windows(
    spans: dict[str, tuple[datetime, datetime]],
) -> tuple[AnalysisWindow, ...]:
    breakpoints = sorted(
        {timestamp for start, end in spans.values() for timestamp in (start, end)}
    )
    return tuple(AnalysisWindow(start, end) for start, end in pairwise(breakpoints))
