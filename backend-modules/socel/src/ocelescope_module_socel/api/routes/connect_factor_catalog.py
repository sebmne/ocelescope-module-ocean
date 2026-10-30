from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import Field

from ocelescope_module_socel.api.dependencies import get_connect_factor_catalog
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.connect_factor_catalog import (
    ConnectFactorCatalog,
    ConnectFactorCatalogCommand,
)
from ocelescope_module_socel.domain.models.factor_catalog import FactorCatalogInfo

router = APIRouter()


class CatalogKeyBody(ApiModel):
    # Text that is not only whitespace.
    key: str = Field(pattern=r"\S", description="The API key the user got from the catalog.")


@router.put(
    "/factor-catalogs/{catalog}/key",
    operation_id="connectFactorCatalog",
    responses={
        404: {"description": "There is no such factor catalog."},
        409: {"description": "The catalog's key is set in the environment (.env)."},
        422: {"description": "The catalog does not accept the key."},
        503: {"description": "The catalog cannot be reached to check the key."},
    },
)
def connect_catalog(
    catalog: str,
    body: CatalogKeyBody,
    use_case: Annotated[ConnectFactorCatalog, Depends(get_connect_factor_catalog)],
) -> FactorCatalogInfo:
    """Check the key with the catalog, and keep it across restarts if it is accepted."""
    return use_case.execute(ConnectFactorCatalogCommand(catalog=catalog, key=body.key))
