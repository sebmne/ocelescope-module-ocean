from dataclasses import dataclass
from datetime import timedelta

import polars as pl
from ocelescope import OCEL
from socel import SOCEL, flow_quantities

from ocelescope_module_socel.analysis.domain.exceptions import NotAnSocelError, UnknownFlowError
from ocelescope_module_socel.analysis.domain.models.flow_series import FlowSeries, WindowQuantity


@dataclass(frozen=True, kw_only=True)
class GetFlowSeriesCommand:
    ocel_id: str
    flow_id: str
    every: timedelta


class GetFlowSeries:
    """A flow's quantity per time window of a fixed length, per meter not nested
    in another."""

    def __init__(self, *, ocel: OCEL) -> None:
        self._ocel = ocel

    def execute(self, command: GetFlowSeriesCommand) -> FlowSeries:
        """Raises:
        NotAnSocelError: The OCEL has no sOCEL tables.
        UnknownFlowError: The sOCEL has no such flow.
        """
        if not SOCEL.is_socel(self._ocel):
            raise NotAnSocelError(f"OCEL {command.ocel_id} has no sOCEL tables.")
        socel = SOCEL(self._ocel)
        flow = socel.flows.filter(pl.col("flow_id") == command.flow_id).collect()
        if flow.is_empty():
            raise UnknownFlowError(f"There is no flow {command.flow_id!r}.")

        quantities = flow_quantities(socel, command.every, flow_id=command.flow_id)
        return FlowSeries(
            flow_id=command.flow_id,
            unit=flow["unit"][0],
            every=command.every,
            windows=tuple(
                WindowQuantity(
                    object_id=row["object_id"],
                    start=row["window_start"],
                    end=row["window_end"],
                    quantity=row["quantity"],
                )
                for row in quantities.iter_rows(named=True)
            ),
        )
