from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_flow_inventory
from ocelescope_module_socel.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
    GetFlowInventoryCommand,
)
from ocelescope_module_socel.domain.models.flow_inventory import FlowSummary

router = APIRouter()


@router.get(
    "/flows",
    operation_id="getFlowInventory",
    responses={422: {"description": "The OCEL is no sOCEL."}},
)
def get_flows(
    use_case: Annotated[GetFlowInventory, Depends(get_flow_inventory)],
) -> tuple[FlowSummary, ...]:
    return use_case.execute(GetFlowInventoryCommand())
