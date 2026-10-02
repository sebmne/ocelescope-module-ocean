from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_class_counts
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.get_class_counts import GetClassCounts
from ocelescope_module_socel.domain.models.class_counts import ClassCount, ClassCounts

router = APIRouter(tags=["sOCEL"])


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


@router.get(
    "/{ocel_id}/classes",
    operation_id="getClassCounts",
    responses={422: {"description": "The OCEL is no sOCEL."}},
)
def get_classes(
    ocel_id: str, use_case: Annotated[GetClassCounts, Depends(get_class_counts)]
) -> ClassCountsModel:
    """How many objects and events carry each socel_class, most frequent first."""
    result = use_case.execute()
    response = ClassCountsModel.from_domain(result)
    return response
