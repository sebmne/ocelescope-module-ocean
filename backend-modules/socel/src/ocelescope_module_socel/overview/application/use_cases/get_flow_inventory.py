from dataclasses import dataclass

import polars as pl
from ocelescope import OCEL
from socel import SOCEL

from ocelescope_module_socel.overview.domain.exceptions import NotAnSocelError
from ocelescope_module_socel.overview.domain.models.flow_inventory import (
    FlowInstanceSummary,
    FlowSummary,
)


@dataclass(frozen=True, kw_only=True)
class GetFlowInventoryCommand:
    ocel_id: str


class GetFlowInventory:
    """The flows of an sOCEL, each with its flow instances: where they sit among the
    metering scopes (containment) and how many records they have."""

    def __init__(self, *, ocel: OCEL) -> None:
        self._ocel = ocel

    def execute(self, command: GetFlowInventoryCommand) -> tuple[FlowSummary, ...]:
        """Raises:
        NotAnSocelError: The OCEL has no sOCEL tables.
        """
        if not SOCEL.is_socel(self._ocel):
            raise NotAnSocelError(f"OCEL {command.ocel_id} has no sOCEL tables.")
        socel = SOCEL(self._ocel)

        records = socel.records.group_by("object_id", "flow_id").agg(
            (pl.col("kind") == "interval").sum().alias("interval_records"),
            (pl.col("kind") == "event").sum().alias("event_records"),
        )
        instances = (
            socel.flow_instances.join(
                socel.objects.select("object_id", "object_type"), on="object_id", how="left"
            )
            .join(socel.contained_in, on=["flow_id", "object_id"], how="left")
            .join(records, on=["object_id", "flow_id"], how="left")
            .with_columns(pl.col("interval_records", "event_records").fill_null(0))
            .sort("object_id")
            .collect()
        )
        by_flow: dict[str, list[FlowInstanceSummary]] = {}
        for row in instances.iter_rows(named=True):
            by_flow.setdefault(row["flow_id"], []).append(
                FlowInstanceSummary(
                    object_id=row["object_id"],
                    object_type=row["object_type"],
                    parent_object_id=row["parent_object_id"],
                    interval_records=row["interval_records"],
                    event_records=row["event_records"],
                )
            )
        return tuple(
            FlowSummary(
                flow_id=flow["flow_id"],
                unit=flow["unit"],
                category=flow["category"],
                external_ref=flow["external_ref"],
                instances=tuple(by_flow.get(flow["flow_id"], ())),
            )
            for flow in socel.flows.sort("flow_id").collect().iter_rows(named=True)
        )
