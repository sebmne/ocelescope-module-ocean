from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_class_taxonomies
from ocelescope_module_socel.application.use_cases.get_class_taxonomies import (
    GetClassTaxonomies,
    GetClassTaxonomiesCommand,
)
from ocelescope_module_socel.domain.models.class_taxonomy import ClassTaxonomies

router = APIRouter()


@router.get("/taxonomy", operation_id="getClassTaxonomies")
def get_taxonomy(
    use_case: Annotated[GetClassTaxonomies, Depends(get_class_taxonomies)],
) -> ClassTaxonomies:
    return use_case.execute(GetClassTaxonomiesCommand())
