from datetime import datetime, timedelta
from typing import Annotated, Literal

from fastapi import APIRouter, Depends

from ocelescope_module_socel.analysis.api.dependencies import get_flow_series
from ocelescope_module_socel.analysis.application.use_cases.get_flow_series import (
    GetFlowSeries,
    GetFlowSeriesCommand,
)
from ocelescope_module_socel.analysis.domain.models.flow_series import FlowSeries, WindowQuantity
from ocelescope_module_socel.api_schema import ApiModel

router = APIRouter(tags=["sOCEL analysis"])

Bucket = Literal["15min", "hour", "day", "week"]
_BUCKETS: dict[str, timedelta] = {
    "15min": timedelta(minutes=15),
    "hour": timedelta(hours=1),
    "day": timedelta(days=1),
    "week": timedelta(weeks=1),
}


class WindowQuantityModel(ApiModel):
    object_id: str
    start: datetime
    end: datetime
    quantity: float

    @classmethod
    def from_domain(cls, window: WindowQuantity) -> "WindowQuantityModel":
        return cls(
            object_id=window.object_id, start=window.start, end=window.end, quantity=window.quantity
        )


class FlowSeriesModel(ApiModel):
    flow_id: str
    unit: str
    windows: list[WindowQuantityModel]

    @classmethod
    def from_domain(cls, series: FlowSeries) -> "FlowSeriesModel":
        return cls(
            flow_id=series.flow_id,
            unit=series.unit,
            windows=[WindowQuantityModel.from_domain(window) for window in series.windows],
        )


@router.get(
    "/{ocel_id}/flows/{flow_id}/series",
    operation_id="getFlowSeries",
    responses={
        404: {"description": "The sOCEL has no such flow."},
        409: {"description": "The OCEL has no sOCEL tables."},
    },
)
def get_series(
    ocel_id: str,
    flow_id: str,
    use_case: Annotated[GetFlowSeries, Depends(get_flow_series)],
    bucket: Bucket = "hour",
) -> FlowSeriesModel:
    """The flow's quantity per time window, per meter not nested in another."""
    command = GetFlowSeriesCommand(ocel_id=ocel_id, flow_id=flow_id, every=_BUCKETS[bucket])
    result = use_case.execute(command)
    response = FlowSeriesModel.from_domain(result)
    return response
