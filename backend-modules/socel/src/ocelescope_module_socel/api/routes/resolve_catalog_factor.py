from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ocelescope_module_socel.api.dependencies import get_resolve_catalog_factor
from ocelescope_module_socel.application.use_cases.resolve_catalog_factor import (
    ResolveCatalogFactor,
    ResolveCatalogFactorCommand,
)
from ocelescope_module_socel.domain.models.factor_catalog import ResolvedFactor

router = APIRouter()


@router.get(
    "/factor-catalogs/{catalog}/factors/{ref:path}",
    operation_id="resolveCatalogFactor",
    responses={
        404: {"description": "There is no such factor catalog, or no such factor in it."},
        422: {"description": "The factor cannot be expressed per the unit."},
        503: {"description": "The catalog is not connected, or cannot be reached."},
    },
)
def resolve_factor(
    catalog: str,
    ref: str,
    # Text that is not only whitespace.
    unit: Annotated[str, Query(pattern=r"\S", description="The flow's unit, e.g. kWh.")],
    use_case: Annotated[ResolveCatalogFactor, Depends(get_resolve_catalog_factor)],
) -> ResolvedFactor:
    """A catalog factor in kg CO2e per one unit of a flow, with where it comes from."""
    return use_case.execute(ResolveCatalogFactorCommand(catalog=catalog, ref=ref, unit=unit))
