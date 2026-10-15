from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field, FiniteFloat

from ocelescope_module_socel.domain.models.base import Model

# The length of the periods a flow's quantity is summed over.
type Period = Literal["hour", "day", "week", "month"]
type Amount = Annotated[FiniteFloat, Field(ge=0)]


class PeriodQuantity(Model):
    """Amounts into and out of objects within one period, both nonnegative."""

    start: datetime
    inflow: Amount
    outflow: Amount


class FlowQuantity(Model):
    """Amounts into and out of objects, counted once, in the flow's unit.

    Records covered by a containing instance's records are excluded by the
    analysis reader. Amounts are nonnegative; direction is explicit.
    """

    flow_id: str
    unit: str
    inflow: Amount
    outflow: Amount
    by_period: tuple[PeriodQuantity, ...]
