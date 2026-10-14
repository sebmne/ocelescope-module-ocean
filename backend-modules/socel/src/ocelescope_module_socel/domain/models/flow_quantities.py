from datetime import datetime
from typing import Literal

from ocelescope_module_socel.domain.models.base import Model

# The length of the periods a flow's quantity is summed over.
type Period = Literal["hour", "day", "week", "month"]


class PeriodQuantity(Model):
    """What a flow's records hold within one period, starting at `start`: the
    amount into the objects and the amount out of them, both positive."""

    start: datetime
    inflow: float
    outflow: float


class FlowQuantity(Model):
    """What a flow's records hold over the log and per period, into the objects
    and out of them (both positive), each quantity counted once: records of an
    instance that lies inside an instance with records of its own are left out,
    as the outer one covers them (thesis, section 7.2.4)."""

    flow_id: str
    unit: str
    inflow: float
    outflow: float
    by_period: tuple[PeriodQuantity, ...]


class DirectionFactors(Model):
    """A flow's factors in kg CO2e per unit: for what flows into the objects
    and for what flows out of them. None counts that direction not at all."""

    inflow: float | None = None
    outflow: float | None = None


class FlowImpact(Model):
    """A flow's amounts in both directions, its factors, and the impact in kg
    CO2e they give; None without any factor."""

    flow_id: str
    unit: str
    inflow: float
    outflow: float
    factors: DirectionFactors
    impact: float | None


class PeriodImpact(Model):
    """The impact of one flow within one period, starting at `start`."""

    start: datetime
    flow_id: str
    impact: float


class ImpactReport(Model):
    """The impact of the flows with a factor: per flow, in all, and per period."""

    flows: tuple[FlowImpact, ...]
    total: float
    by_period: tuple[PeriodImpact, ...]
