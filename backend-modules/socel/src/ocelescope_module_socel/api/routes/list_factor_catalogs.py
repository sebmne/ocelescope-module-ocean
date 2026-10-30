from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_list_factor_catalogs
from ocelescope_module_socel.application.use_cases.list_factor_catalogs import (
    ListFactorCatalogs,
    ListFactorCatalogsCommand,
)
from ocelescope_module_socel.domain.models.factor_catalog import FactorCatalogInfo

router = APIRouter()


@router.get("/factor-catalogs", operation_id="listFactorCatalogs")
def list_catalogs(
    use_case: Annotated[ListFactorCatalogs, Depends(get_list_factor_catalogs)],
) -> tuple[FactorCatalogInfo, ...]:
    """The external databases of emission factors, and whether each can be consulted."""
    return use_case.execute(ListFactorCatalogsCommand())
