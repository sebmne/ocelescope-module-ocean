from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ActivityQuantity:
    """How much of a flow the operations of one activity were attributed."""

    activity: str
    quantity: float
    operations: int


@dataclass(frozen=True, kw_only=True)
class MeterAttribution:
    """A meter of a flow: what it recorded, and how much of that reached an
    operation. `nested`: the meter lies within another, so the flow's totals
    leave it out (its parent already recorded it)."""

    object_id: str
    object_type: str
    nested: bool
    recorded: float
    attributed: float
    remainder: float


@dataclass(frozen=True, kw_only=True)
class FlowAttribution:
    """A flow attributed to the operations it was recorded during. Totals and
    activities are over the meters not nested in another, so nothing counts
    twice; recorded = attributed + remainder."""

    flow_id: str
    unit: str
    recorded: float
    attributed: float
    remainder: float
    activities: tuple[ActivityQuantity, ...]
    meters: tuple[MeterAttribution, ...]
