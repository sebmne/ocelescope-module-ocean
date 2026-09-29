from dataclasses import dataclass
from datetime import datetime, timedelta


@dataclass(frozen=True, kw_only=True)
class WindowQuantity:
    """What one meter recorded of a flow within one time window."""

    object_id: str
    start: datetime
    end: datetime
    quantity: float


@dataclass(frozen=True, kw_only=True)
class FlowSeries:
    """A flow over time, per window and meter not nested in another, so the
    quantities of a window add up to the flow's quantity in it. Windows without
    records are missing: a gap in the data, not a zero."""

    flow_id: str
    unit: str
    every: timedelta
    windows: tuple[WindowQuantity, ...]
