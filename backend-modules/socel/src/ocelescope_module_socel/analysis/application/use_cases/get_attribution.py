from dataclasses import dataclass

import polars as pl
from ocelescope import OCEL
from socel import SOCEL, attribute

from ocelescope_module_socel.analysis.application.ports.settings_repository import (
    SettingsRepository,
)
from ocelescope_module_socel.analysis.domain.exceptions import NotAnSocelError
from ocelescope_module_socel.analysis.domain.models.flow_attribution import (
    ActivityQuantity,
    FlowAttribution,
    MeterAttribution,
)


@dataclass(frozen=True, kw_only=True)
class GetAttributionCommand:
    ocel_id: str


class GetAttribution:
    """Attributes every flow's records to the operations they were recorded
    during (group metering as the settings say), summed per flow, activity and
    meter."""

    def __init__(self, *, ocel: OCEL, settings: SettingsRepository) -> None:
        self._ocel = ocel
        self._settings = settings

    def execute(self, command: GetAttributionCommand) -> tuple[FlowAttribution, ...]:
        """Raises:
        NotAnSocelError: The OCEL has no sOCEL tables.
        """
        if not SOCEL.is_socel(self._ocel):
            raise NotAnSocelError(f"OCEL {command.ocel_id} has no sOCEL tables.")
        socel = SOCEL(self._ocel)
        settings = self._settings.get(command.ocel_id)
        result = attribute(socel, group_metering=settings.group_metering)

        meters = result.by_instance.join(
            socel.objects.select("object_id", "object_type").collect(), on="object_id", how="left"
        ).with_columns((~pl.col("top_level")).alias("nested"))
        counted = meters.filter(~pl.col("nested")).select("flow_id", "object_id")
        activities = (
            result.by_event.join(counted, on=["flow_id", "object_id"])
            .join(socel.events.select("event_id", "activity").collect(), on="event_id")
            .group_by("flow_id", "activity")
            .agg(pl.col("quantity").sum(), pl.col("event_id").n_unique().alias("operations"))
            .sort(pl.col("quantity").abs(), descending=True)
        )

        return tuple(
            _flow(flow, meters, activities)
            for flow in socel.flows.sort("flow_id").collect().iter_rows(named=True)
        )


def _flow(flow: dict[str, str], meters: pl.DataFrame, activities: pl.DataFrame) -> FlowAttribution:
    flow_id = flow["flow_id"]
    own = meters.filter(pl.col("flow_id") == flow_id).sort(
        ["nested", "recorded"], descending=[False, True]
    )
    totals = own.filter(~pl.col("nested")).select(
        pl.col("recorded", "attributed", "remainder").sum()
    )
    return FlowAttribution(
        flow_id=flow_id,
        unit=flow["unit"],
        recorded=float(totals["recorded"][0]),
        attributed=float(totals["attributed"][0]),
        remainder=float(totals["remainder"][0]),
        activities=tuple(
            ActivityQuantity(
                activity=row["activity"], quantity=row["quantity"], operations=row["operations"]
            )
            for row in activities.filter(pl.col("flow_id") == flow_id).iter_rows(named=True)
        ),
        meters=tuple(
            MeterAttribution(
                object_id=row["object_id"],
                object_type=row["object_type"],
                nested=row["nested"],
                recorded=row["recorded"],
                attributed=row["attributed"],
                remainder=row["remainder"],
            )
            for row in own.iter_rows(named=True)
        ),
    )
