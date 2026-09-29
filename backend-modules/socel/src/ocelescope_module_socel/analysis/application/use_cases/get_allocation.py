from dataclasses import dataclass

import polars as pl
from ocelescope import OCEL

from ocelescope_module_socel.analysis.application.flow_trace import trace_flows
from ocelescope_module_socel.analysis.application.ports.settings_repository import (
    SettingsRepository,
)
from ocelescope_module_socel.analysis.domain.models.flow_allocation import (
    AllocationOverview,
    FlowAllocation,
    UnitAllocation,
)

# The largest shares per flow sent along; the counts say how many there are.
_TOP_UNITS = 20


@dataclass(frozen=True, kw_only=True)
class GetAllocationCommand:
    ocel_id: str


class GetAllocation:
    """Every flow allocated to the handling units of its operations and, with a
    lineage in the settings, carried down to the units created from them."""

    def __init__(self, *, ocel: OCEL, settings: SettingsRepository) -> None:
        self._ocel = ocel
        self._settings = settings

    def execute(self, command: GetAllocationCommand) -> AllocationOverview:
        """Raises:
        NotAnSocelError: The OCEL has no sOCEL tables.
        """
        trace = trace_flows(self._ocel, command.ocel_id, self._settings.get(command.ocel_id))
        types = trace.socel.objects.select("object_id", "object_type").collect()
        units = trace.allocation.by_unit.rename({"quantity": "allocated"})
        if trace.carried is not None:
            units = units.join(
                trace.carried.rename({"quantity": "carried"}),
                on=["flow_id", "object_id"],
                how="full",
                coalesce=True,
            ).with_columns(pl.col("allocated").fill_null(0.0))
        else:
            units = units.with_columns(
                pl.lit(None, pl.Float64).alias("carried"), pl.lit(True).alias("is_end")
            )
        units = units.join(types, on="object_id", how="left").with_columns(
            pl.coalesce("carried", "allocated").abs().alias("_size")
        )
        flows = trace.socel.flows.select("flow_id", "unit").collect()

        return AllocationOverview(
            flows=tuple(
                _flow(
                    f["flow_id"],
                    f["unit"],
                    _totals(trace.allocation.by_flow, f["flow_id"]),
                    units.filter(pl.col("flow_id") == f["flow_id"]),
                )
                for f in flows.sort("flow_id").iter_rows(named=True)
            ),
            has_lineage=trace.carried is not None,
            lineage_problem=trace.lineage_problem,
        )


def _totals(by_flow: pl.DataFrame, flow_id: str) -> dict[str, float]:
    row = by_flow.filter(pl.col("flow_id") == flow_id)
    names = ("recorded", "attributed", "allocated", "unallocated")
    return {n: float(row[n][0]) if not row.is_empty() else 0.0 for n in names}


def _flow(flow_id: str, unit: str, totals: dict[str, float], units: pl.DataFrame) -> FlowAllocation:
    # With a lineage, what the end units carry is the result.
    if units["carried"].is_not_null().any():
        units = units.filter(pl.col("is_end"))
    top = units.sort("_size", descending=True).head(_TOP_UNITS)
    return FlowAllocation(
        flow_id=flow_id,
        unit=unit,
        recorded=totals["recorded"],
        attributed=totals["attributed"],
        allocated=totals["allocated"],
        unallocated=totals["unallocated"],
        units=tuple(
            UnitAllocation(
                object_id=row["object_id"],
                object_type=row["object_type"],
                allocated=row["allocated"],
                carried=row["carried"],
                is_end_unit=row["is_end"],
            )
            for row in top.iter_rows(named=True)
        ),
        unit_count=units.height,
    )
