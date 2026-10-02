from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_socel_status
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.get_socel_status import GetSocelStatus
from ocelescope_module_socel.domain.models.socel_status import SocelStatus

router = APIRouter(tags=["sOCEL"])


class SocelStatusModel(ApiModel):
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


@router.get(
    "/{ocel_id}/status",
    operation_id="getSocelStatus",
    responses={422: {"description": "The OCEL is no sOCEL."}},
)
def get_status(
    ocel_id: str, use_case: Annotated[GetSocelStatus, Depends(get_socel_status)]
) -> SocelStatusModel:
    """What the sOCEL holds, in counts, and the period its records span."""
    result = use_case.execute()
    response = SocelStatusModel.from_domain(result)
    return response
