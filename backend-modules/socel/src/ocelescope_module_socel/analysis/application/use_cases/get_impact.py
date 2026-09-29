from dataclasses import dataclass

import polars as pl
from ocelescope import OCEL
from socel import impact

from ocelescope_module_socel.analysis.application.flow_trace import FlowTrace, trace_flows
from ocelescope_module_socel.analysis.application.ports.settings_repository import (
    SettingsRepository,
)
from ocelescope_module_socel.analysis.domain.models.impact_overview import (
    ActivityImpact,
    EndUnitFootprint,
    FlowImpact,
    FootprintBin,
    ImpactOverview,
)

_TOP_END_UNITS = 20
_BINS = 12


@dataclass(frozen=True, kw_only=True)
class GetImpactCommand:
    ocel_id: str


class GetImpact:
    """The traced flows in kg CO2e, with the settings' emission factors: per
    flow, per activity, and what the end units of the lineage carry."""

    def __init__(self, *, ocel: OCEL, settings: SettingsRepository) -> None:
        self._ocel = ocel
        self._settings = settings

    def execute(self, command: GetImpactCommand) -> ImpactOverview:
        """Raises:
        NotAnSocelError: The OCEL has no sOCEL tables.
        """
        settings = self._settings.get(command.ocel_id)
        trace = trace_flows(self._ocel, command.ocel_id, settings)
        factors = {f.flow_id: f.impact_per_unit for f in settings.emission_factors}
        units = dict(trace.socel.flows.select("flow_id", "unit").collect().iter_rows())

        by_flow = trace.allocation.by_flow.filter(pl.col("flow_id").is_in(list(factors)))
        flows = tuple(
            FlowImpact(
                flow_id=row["flow_id"],
                unit=units.get(row["flow_id"], ""),
                impact_per_unit=factors[row["flow_id"]],
                recorded=factors[row["flow_id"]] * row["recorded"],
                attributed=factors[row["flow_id"]] * row["attributed"],
                allocated=factors[row["flow_id"]] * row["allocated"],
            )
            for row in by_flow.iter_rows(named=True)
        )

        events = trace.socel.events.select("event_id", "activity").collect()
        activities = (
            impact(trace.allocation.by_event, factors, ["event_id"])
            .join(events, on="event_id")
            .group_by("activity")
            .agg(pl.col("impact").sum(), pl.len().alias("operations"))
            .filter(pl.col("impact") != 0)
            .sort(pl.col("impact").abs(), descending=True)
        )

        end_units = _end_units(trace, factors)
        per_kg = end_units["footprint_per_kg"].drop_nulls()
        median = per_kg.median()
        return ImpactOverview(
            recorded=sum(f.recorded for f in flows),
            attributed=sum(f.attributed for f in flows),
            allocated=sum(f.allocated for f in flows),
            flows=flows,
            activities=tuple(
                ActivityImpact(
                    activity=r["activity"], impact=r["impact"], operations=r["operations"]
                )
                for r in activities.iter_rows(named=True)
            ),
            end_units=tuple(
                EndUnitFootprint(
                    object_id=r["object_id"],
                    object_type=r["object_type"],
                    footprint=r["footprint"],
                    mass=r["mass"],
                    footprint_per_kg=r["footprint_per_kg"],
                )
                for r in end_units.sort(
                    "footprint_per_kg", "footprint", descending=True, nulls_last=True
                )
                .head(_TOP_END_UNITS)
                .iter_rows(named=True)
            ),
            end_unit_count=end_units.height,
            median_footprint_per_kg=float(median) if isinstance(median, int | float) else None,
            footprint_bins=_bins(per_kg),
            lineage_problem=trace.lineage_problem,
        )


def _end_units(trace: FlowTrace, factors: dict[str, float]) -> pl.DataFrame:
    """What the end units carry in kg CO2e, with their mass and per kg."""
    schema = {
        "object_id": pl.String,
        "object_type": pl.String,
        "footprint": pl.Float64,
        "mass": pl.Float64,
        "footprint_per_kg": pl.Float64,
    }
    if trace.carried is None or trace.parent is None:
        return pl.DataFrame(schema=schema)
    # Every handling unit without children is an end unit, with 0 where nothing arrived.
    ends = (
        trace.socel.handling_units.select("object_id", "object_type")
        .collect()
        .filter(~pl.col("object_id").is_in(trace.parent["parent_object_id"].implode()))
    )
    carried = impact(trace.carried.filter(pl.col("is_end")), factors, ["object_id"])
    footprints = ends.join(carried.rename({"impact": "footprint"}), on="object_id", how="left")
    masses = (
        trace.masses.rename({"value": "mass"})
        if trace.masses is not None
        else pl.DataFrame(schema={"object_id": pl.String, "mass": pl.Float64})
    )
    return (
        footprints.with_columns(pl.col("footprint").fill_null(0.0))
        .join(masses, on="object_id", how="left")
        .with_columns(
            pl.when(pl.col("mass") > 0)
            .then(pl.col("footprint") / pl.col("mass"))
            .alias("footprint_per_kg")
        )
        .select(list(schema))
    )


def _bins(values: pl.Series) -> tuple[FootprintBin, ...]:
    """Equal-width bins over the footprints per kg, for a histogram."""
    if len(values) < 2:
        return ()
    numbers = [float(v) for v in values.to_list()]
    low, high = min(numbers), max(numbers)
    if low == high:
        return (FootprintBin(lower=low, upper=high, end_units=len(numbers)),)
    width = (high - low) / _BINS
    counts = [0] * _BINS
    for value in numbers:
        counts[min(int((value - low) / width), _BINS - 1)] += 1
    return tuple(
        FootprintBin(lower=low + i * width, upper=low + (i + 1) * width, end_units=n)
        for i, n in enumerate(counts)
    )
