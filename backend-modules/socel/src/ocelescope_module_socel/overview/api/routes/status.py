from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api_schema import ApiModel
from ocelescope_module_socel.overview.api.dependencies import get_socel_status
from ocelescope_module_socel.overview.application.use_cases.get_socel_status import (
    GetSocelStatus,
    GetSocelStatusCommand,
)
from ocelescope_module_socel.overview.domain.models.socel_status import SocelStatus

router = APIRouter(tags=["sOCEL overview"])


class SocelStatusModel(ApiModel):
    ocel_name: str
    is_socel: bool
    objects: int
    events: int
    handling_units: int
    operations: int
    flows: int
    flow_instances: int
    interval_records: int
    event_records: int
    containments: int
    records_from: datetime | None
    records_to: datetime | None

    @classmethod
    def from_domain(cls, status: SocelStatus) -> "SocelStatusModel":
        return cls(
            ocel_name=status.ocel_name,
            is_socel=status.is_socel,
            objects=status.objects,
            events=status.events,
            handling_units=status.handling_units,
            operations=status.operations,
            flows=status.flows,
            flow_instances=status.flow_instances,
            interval_records=status.interval_records,
            event_records=status.event_records,
            containments=status.containments,
            records_from=status.records_from,
            records_to=status.records_to,
        )


@router.get("/{ocel_id}/status", operation_id="getSocelStatus")
def get_status(
    ocel_id: str, use_case: Annotated[GetSocelStatus, Depends(get_socel_status)]
) -> SocelStatusModel:
    """Whether the OCEL is an sOCEL, and what it holds: counts, no validation."""
    command = GetSocelStatusCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = SocelStatusModel.from_domain(result)
    return response
