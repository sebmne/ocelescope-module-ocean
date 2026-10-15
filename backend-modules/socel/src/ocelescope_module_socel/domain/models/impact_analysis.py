from datetime import datetime

from pydantic import FiniteFloat

from ocelescope_module_socel.domain.models.base import Model
from ocelescope_module_socel.domain.models.flow_quantities import Amount, Period


class DirectionFactors(Model):
    """kg CO2e per flow unit, selected independently for each direction.

    An absent factor excludes that direction. Zero is a selected factor;
    negative factors are allowed, for example for credits.
    """

    inflow: FiniteFloat | None = None
    outflow: FiniteFloat | None = None

    def apply(self, *, inflow: float, outflow: float) -> float | None:
        """Apply factors to nonnegative directional amounts, not a signed net."""
        if self.inflow is None and self.outflow is None:
            return None
        return (self.inflow * inflow if self.inflow is not None else 0.0) + (
            self.outflow * outflow if self.outflow is not None else 0.0
        )


class ImpactAnalysis(Model):
    """Analysis choices; factors for flows absent from the log are ignored."""

    period: Period = "day"
    factors: dict[str, DirectionFactors]


class FlowImpact(Model):
    """A flow's amounts and selected factors, with its impact in kg CO2e."""

    flow_id: str
    unit: str
    inflow: Amount
    outflow: Amount
    factors: DirectionFactors
    impact: FiniteFloat | None


class PeriodImpact(Model):
    """The impact of one flow within a period starting at `start`."""

    start: datetime
    flow_id: str
    impact: FiniteFloat


class ImpactReport(Model):
    """Selected flows' impact per flow, in total, and per period, in kg CO2e."""

    flows: tuple[FlowImpact, ...]
    total: FiniteFloat
    by_period: tuple[PeriodImpact, ...]
