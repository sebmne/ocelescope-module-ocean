from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_configure_socel
from ocelescope_module_socel.application.use_cases.configure_socel import (
    ConfigureSocel,
    ConfigureSocelCommand,
)
from ocelescope_module_socel.domain.models.preparation import PreparationDraft

router = APIRouter()


@router.patch(
    "/socel",
    operation_id="configureSocel",
    status_code=204,
    responses={422: {"description": "The log cannot be changed as asked."}},
)
def configure_socel(
    preparation: PreparationDraft,
    use_case: Annotated[ConfigureSocel, Depends(get_configure_socel)],
) -> None:
    """Apply partial changes to the original log, keeping its identity and name.

    Types not named keep their class; None removes it. Flow edits precede new
    records. The original log is used regardless of the app's current filters.
    """
    use_case.execute(ConfigureSocelCommand(preparation=preparation))
