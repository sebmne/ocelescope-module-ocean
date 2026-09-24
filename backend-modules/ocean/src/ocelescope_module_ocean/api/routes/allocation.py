from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_ocean.api.dependencies import get_allocate_emissions, get_object_emissions
from ocelescope_module_ocean.api.schema import ApiModel
from ocelescope_module_ocean.application.use_cases.allocate_emissions import (
    AllocateEmissions,
    AllocateEmissionsCommand,
)
from ocelescope_module_ocean.application.use_cases.get_object_emissions import (
    GetObjectEmissions,
    GetObjectEmissionsCommand,
)
from ocelescope_module_ocean.domain.models.allocation import (
    AllocationConfig,
    AllocationRule,
    AllocationSummary,
)

router = APIRouter(tags=["Allocation"])


# ---- Transport models --------------------------------------------------------


class AllocationConfigModel(ApiModel):
    """How to allocate: sent to allocate, and returned with the result."""

    target_object_types: list[str]
    rule: AllocationRule
    pass_via_resources: bool = False
    pass_between_same_type: bool = True

    def to_domain(self) -> AllocationConfig:
        return AllocationConfig(
            target_object_types=tuple(self.target_object_types),
            rule=self.rule,
            pass_via_resources=self.pass_via_resources,
            pass_between_same_type=self.pass_between_same_type,
        )

    @classmethod
    def from_domain(cls, config: AllocationConfig) -> "AllocationConfigModel":
        return cls(
            target_object_types=list(config.target_object_types),
            rule=config.rule,
            pass_via_resources=config.pass_via_resources,
            pass_between_same_type=config.pass_between_same_type,
        )


class HistogramBinResponse(ApiModel):
    lower_kg: float
    upper_kg: float
    objects: int


class AllocationStepsResponse(ApiModel):
    """kg assigned by each step of the allocation."""

    direct_kg: float
    rule_kg: float
    fallback_kg: float


class ObjectEmissionsResponse(ApiModel):
    config: AllocationConfigModel
    total_kg: float
    target_objects: int
    steps: AllocationStepsResponse
    histogram: list[HistogramBinResponse]

    @classmethod
    def from_domain(cls, result: AllocationSummary) -> "ObjectEmissionsResponse":
        return cls(
            config=AllocationConfigModel.from_domain(result.config),
            total_kg=result.total_kg,
            target_objects=result.target_objects,
            steps=AllocationStepsResponse(
                direct_kg=result.steps.direct_kg,
                rule_kg=result.steps.rule_kg,
                fallback_kg=result.steps.fallback_kg,
            ),
            histogram=[
                HistogramBinResponse(lower_kg=b.lower_kg, upper_kg=b.upper_kg, objects=b.objects)
                for b in result.histogram
            ],
        )


# ---- Routes ------------------------------------------------------------------


@router.get("/{ocel_id}/allocation", operation_id="getObjectEmissions")
def get_allocation(
    ocel_id: str,
    use_case: Annotated[GetObjectEmissions, Depends(get_object_emissions)],
) -> ObjectEmissionsResponse | None:
    """The current allocation of the OCEL's emissions; null until they are allocated."""
    command = GetObjectEmissionsCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = ObjectEmissionsResponse.from_domain(result) if result else None
    return response


@router.post(
    "/{ocel_id}/allocation",
    operation_id="allocateEmissions",
    responses={
        409: {"description": "No emissions were computed yet."},
        422: {"description": "The target object types have no objects."},
    },
)
def allocate_emissions(
    ocel_id: str,
    body: AllocationConfigModel,
    use_case: Annotated[AllocateEmissions, Depends(get_allocate_emissions)],
) -> ObjectEmissionsResponse:
    """Allocates the OCEL's computed emissions to the objects of the target types."""
    command = AllocateEmissionsCommand(ocel_id=ocel_id, config=body.to_domain())
    result = use_case.execute(command)
    response = ObjectEmissionsResponse.from_domain(result)
    return response
