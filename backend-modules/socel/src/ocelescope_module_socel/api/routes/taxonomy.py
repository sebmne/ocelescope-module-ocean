from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_class_taxonomies
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.get_class_taxonomies import (
    GetClassTaxonomies,
    GetClassTaxonomiesCommand,
)
from ocelescope_module_socel.domain.models.class_taxonomy import ClassNode, ClassTaxonomies

router = APIRouter(tags=["sOCEL"])


class ClassNodeModel(ApiModel):
    path: str
    label: str
    children: list["ClassNodeModel"]

    @classmethod
    def from_domain(cls, node: ClassNode) -> "ClassNodeModel":
        return cls(
            path=node.path,
            label=node.label,
            children=[cls.from_domain(child) for child in node.children],
        )


class ClassTaxonomiesModel(ApiModel):
    event_classes: list[ClassNodeModel]
    object_classes: list[ClassNodeModel]
    flow_categories: list[ClassNodeModel]

    @classmethod
    def from_domain(cls, taxonomies: ClassTaxonomies) -> "ClassTaxonomiesModel":
        return cls(
            event_classes=[ClassNodeModel.from_domain(n) for n in taxonomies.event_classes],
            object_classes=[ClassNodeModel.from_domain(n) for n in taxonomies.object_classes],
            flow_categories=[ClassNodeModel.from_domain(n) for n in taxonomies.flow_categories],
        )


@router.get("/taxonomy", operation_id="getClassTaxonomies")
def get_taxonomy(
    use_case: Annotated[GetClassTaxonomies, Depends(get_class_taxonomies)],
) -> ClassTaxonomiesModel:
    """The classes an sOCEL may give its events and its objects, and the
    categories it may give its flows, as trees."""
    result = use_case.execute(GetClassTaxonomiesCommand())
    response = ClassTaxonomiesModel.from_domain(result)
    return response
