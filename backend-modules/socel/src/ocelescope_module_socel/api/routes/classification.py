from typing import Annotated

from fastapi import APIRouter, Depends
from ocelescope_backend.app.dependencies import ApiOcel

from ocelescope_module_socel.api.dependencies import get_build_socel, get_log_classification
from ocelescope_module_socel.api.routes.flow_records import FlowDefinitionModel
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.build_socel import (
    BuildSocel,
    BuildSocelCommand,
    RecordsToImport,
)
from ocelescope_module_socel.application.use_cases.get_log_classification import (
    GetLogClassification,
    GetLogClassificationCommand,
)
from ocelescope_module_socel.domain.models.log_classification import (
    LogClassification,
    TypeClassification,
)

router = APIRouter(tags=["sOCEL"])


class TypeClassificationModel(ApiModel):
    name: str
    count: int
    # None when its events or objects carry no class, or not all the same one.
    socel_class: str | None

    @classmethod
    def from_domain(cls, item: TypeClassification) -> "TypeClassificationModel":
        return cls(name=item.name, count=item.count, socel_class=item.socel_class)


class LogClassificationModel(ApiModel):
    activities: list[TypeClassificationModel]
    object_types: list[TypeClassificationModel]

    @classmethod
    def from_domain(cls, classification: LogClassification) -> "LogClassificationModel":
        return cls(
            activities=[TypeClassificationModel.from_domain(a) for a in classification.activities],
            object_types=[
                TypeClassificationModel.from_domain(t) for t in classification.object_types
            ],
        )


class RecordsToImportModel(ApiModel):
    # The id an uploaded record file is kept under, and unit and category of
    # each of its flows.
    upload_id: str
    flows: dict[str, FlowDefinitionModel]

    def to_domain(self) -> RecordsToImport:
        return RecordsToImport(
            upload_id=self.upload_id,
            flows={flow_id: flow.to_domain() for flow_id, flow in self.flows.items()},
        )


class BuildSocelRequest(ApiModel):
    name: str
    # Class per activity and per object type; null takes a class away. Types not
    # named keep what they have.
    activities: dict[str, str | None]
    object_types: dict[str, str | None]
    records: RecordsToImportModel | None = None


class BuiltSocelModel(ApiModel):
    ocel_id: str


@router.get("/{ocel_id}/classification", operation_id="getLogClassification")
def get_classification(
    ocel: ApiOcel,
    use_case: Annotated[GetLogClassification, Depends(get_log_classification)],
) -> LogClassificationModel:
    """How the log's activities and object types are classified now. Any log may
    be asked, an sOCEL or not."""
    result = use_case.execute(GetLogClassificationCommand(ocel=ocel))
    response = LogClassificationModel.from_domain(result)
    return response


@router.post(
    "/{ocel_id}/socel",
    operation_id="buildSocel",
    responses={422: {"description": "The log cannot be turned into an sOCEL as asked."}},
)
def build_socel(
    ocel: ApiOcel,
    request: BuildSocelRequest,
    use_case: Annotated[BuildSocel, Depends(get_build_socel)],
) -> BuiltSocelModel:
    """Adds a new log to the session: the given one as an sOCEL, classified per
    activity and object type, with the flow records of an uploaded file."""
    ocel_id = use_case.execute(
        BuildSocelCommand(
            ocel=ocel,
            name=request.name,
            activities=request.activities,
            object_types=request.object_types,
            records=request.records.to_domain() if request.records else None,
        )
    )
    response = BuiltSocelModel(ocel_id=ocel_id)
    return response
