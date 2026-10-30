from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ocelescope_module_socel.api.dependencies import get_search_factor_catalog
from ocelescope_module_socel.api.models.pagination import Page, Pagination
from ocelescope_module_socel.application.use_cases.search_factor_catalog import (
    SearchFactorCatalog,
    SearchFactorCatalogCommand,
)
from ocelescope_module_socel.domain.models.factor_catalog import CatalogFactor

router = APIRouter()


@router.get(
    "/factor-catalogs/{catalog}/factors",
    operation_id="searchFactorCatalog",
    responses={
        404: {"description": "There is no such factor catalog."},
        422: {"description": "The search or pagination is invalid."},
        503: {"description": "The catalog is not connected, or cannot be reached."},
    },
)
def search_factors(
    catalog: str,
    # Text that is not only whitespace.
    text: Annotated[str, Query(pattern=r"\S", description="What to look for.")],
    use_case: Annotated[SearchFactorCatalog, Depends(get_search_factor_catalog)],
    pagination: Annotated[Pagination, Depends()],
    unit: Annotated[
        str | None, Query(description="Keep factors that can be expressed per this unit.")
    ] = None,
    region: Annotated[str | None, Query(description="Keep factors for this region.")] = None,
    year: Annotated[int | None, Query(ge=1, description="Keep factors for this year.")] = None,
) -> Page[CatalogFactor]:
    """Factors of the catalog matching the search, best match first, as it lists them."""
    items, total = use_case.execute(
        SearchFactorCatalogCommand(
            catalog=catalog,
            text=text,
            unit=unit,
            region=region,
            year=year,
            offset=pagination.offset,
            limit=pagination.limit,
        )
    )
    return Page[CatalogFactor].from_result(pagination, items, total)
