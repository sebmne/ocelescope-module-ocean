from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response
from pydantic import StringConstraints

from ocelescope_module_socel.api.dependencies import get_build_socel
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.build_socel import BuildSocel, BuildSocelCommand
from ocelescope_module_socel.domain.models.preparation import PreparationDraft


class BuildSocelRequest(PreparationDraft):
    """Flat HTTP body combining domain preparation with the new host log's name."""

    name: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class CreatedLog(ApiModel):
    """HTTP representation of the host identifier returned by creation."""

    ocel_id: str


router = APIRouter()


@router.post(
    "/derivations",
    status_code=201,
    operation_id="buildSocel",
    responses={422: {"description": "The log cannot be turned into an sOCEL as asked."}},
)
def build_socel(
    request: Request,
    response: Response,
    body: BuildSocelRequest,
    use_case: Annotated[BuildSocel, Depends(get_build_socel)],
) -> CreatedLog:
    """Build from the host's selected view and publish a new log beside its source."""
    preparation = PreparationDraft.model_validate(body.model_dump(exclude={"name"}, by_alias=False))
    ocel_id = use_case.execute(BuildSocelCommand(name=body.name, preparation=preparation))
    response.headers["Location"] = str(request.url_for("socel-summary", ocel_id=ocel_id))
    return CreatedLog(ocel_id=ocel_id)
