from typing import Annotated

from fastapi import APIRouter, Depends, Response

from ocelescope_module_socel.api.dependencies import get_disconnect_factor_catalog
from ocelescope_module_socel.application.use_cases.disconnect_factor_catalog import (
    DisconnectFactorCatalog,
    DisconnectFactorCatalogCommand,
)

router = APIRouter()


@router.delete(
    "/factor-catalogs/{catalog}/key",
    operation_id="disconnectFactorCatalog",
    status_code=204,
    responses={
        404: {"description": "There is no such factor catalog."},
        409: {"description": "The catalog's key is set in the environment (.env)."},
    },
)
def disconnect_catalog(
    catalog: str,
    use_case: Annotated[DisconnectFactorCatalog, Depends(get_disconnect_factor_catalog)],
) -> Response:
    """Forget the key kept for the catalog."""
    use_case.execute(DisconnectFactorCatalogCommand(catalog=catalog))
    return Response(status_code=204)
