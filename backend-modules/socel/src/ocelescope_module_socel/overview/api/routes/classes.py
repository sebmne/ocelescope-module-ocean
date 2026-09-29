from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api_schema import ApiModel
from ocelescope_module_socel.overview.api.dependencies import get_class_counts
from ocelescope_module_socel.overview.application.use_cases.get_class_counts import (
    GetClassCounts,
    GetClassCountsCommand,
)
from ocelescope_module_socel.overview.domain.models.class_counts import ClassCount, ClassCounts

router = APIRouter(tags=["sOCEL overview"])


class ClassCountModel(ApiModel):
    socel_class: str | None
    count: int
    # Handling-unit classes for objects, operation classes for events.
    is_core: bool

    @classmethod
    def from_domain(cls, count: ClassCount) -> "ClassCountModel":
        return cls(socel_class=count.socel_class, count=count.count, is_core=count.is_core)


class ClassCountsModel(ApiModel):
    objects: list[ClassCountModel]
    events: list[ClassCountModel]

    @classmethod
    def from_domain(cls, counts: ClassCounts) -> "ClassCountsModel":
        return cls(
            objects=[ClassCountModel.from_domain(c) for c in counts.objects],
            events=[ClassCountModel.from_domain(c) for c in counts.events],
        )


@router.get("/{ocel_id}/classes", operation_id="getClassCounts")
def get_classes(
    ocel_id: str, use_case: Annotated[GetClassCounts, Depends(get_class_counts)]
) -> ClassCountsModel:
    """How many objects and events carry each socel_class, most frequent first."""
    command = GetClassCountsCommand(ocel_id=ocel_id)
    result = use_case.execute(command)
    response = ClassCountsModel.from_domain(result)
    return response
