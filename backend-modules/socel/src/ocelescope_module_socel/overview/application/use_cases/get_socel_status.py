from dataclasses import dataclass

import polars as pl
from ocelescope import OCEL
from socel import SOCEL

from ocelescope_module_socel.overview.application.ports.ocel_catalog import OcelCatalog
from ocelescope_module_socel.overview.domain.models.socel_status import SocelStatus


@dataclass(frozen=True, kw_only=True)
class GetSocelStatusCommand:
    ocel_id: str


class GetSocelStatus:
    """What the OCEL holds as an sOCEL; cheap, as it only counts."""

    def __init__(self, *, ocel: OCEL, catalog: OcelCatalog) -> None:
        self._ocel = ocel
        self._catalog = catalog

    def execute(self, command: GetSocelStatusCommand) -> SocelStatus:
        socel = SOCEL(self._ocel)
        name = self._catalog.name(command.ocel_id)
        objects, events = socel.objects, socel.events
        handling_units = _count(objects.filter(pl.col("is_handling_unit")))
        operations = _count(events.filter(pl.col("is_operation")))
        if not SOCEL.is_socel(self._ocel):
            return SocelStatus(
                ocel_name=name,
                is_socel=False,
                objects=_count(objects),
                events=_count(events),
                handling_units=handling_units,
                operations=operations,
            )

        start, end = (
            socel.records.select(
                pl.col("start_time").min(), pl.coalesce("end_time", "start_time").max()
            )
            .collect()
            .row(0)
        )
        return SocelStatus(
            ocel_name=name,
            is_socel=True,
            objects=_count(objects),
            events=_count(events),
            handling_units=handling_units,
            operations=operations,
            flows=_count(socel.flows),
            flow_instances=_count(socel.flow_instances),
            interval_records=_count(socel.interval_records),
            event_records=_count(socel.event_records),
            containments=_count(socel.contained_in),
            records_from=start,
            records_to=end,
        )


def _count(frame: pl.LazyFrame) -> int:
    return int(frame.select(pl.len()).collect().item())
