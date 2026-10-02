"""Measurements recorded for flow instances."""

from dataclasses import dataclass
from datetime import datetime

from socel.domain.flow_instance import FlowInstance


@dataclass(frozen=True, slots=True)
class IntervalRecord:
    """A quantity observed over a time interval."""

    id: str
    instance: FlowInstance
    quantity: float
    start: datetime
    end: datetime


@dataclass(frozen=True, slots=True)
class EventRecord:
    """A quantity associated with an OCEL event."""

    id: str
    instance: FlowInstance
    quantity: float
    event_id: str


type FlowRecord = IntervalRecord | EventRecord
