from typing import Annotated

from fastapi import APIRouter, Depends
from ocelescope_backend.app.dependencies import ApiOcel
from pydantic import Field

from ocelescope_module_socel.api.dependencies import (
    get_build_socel,
    get_configure_socel,
    get_log_classification,
)
from ocelescope_module_socel.api.routes.flow_records import (
    ColumnMappingModel,
    FlowDefinitionModel,
)
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.build_socel import (
    BuildSocel,
    BuildSocelCommand,
)
from ocelescope_module_socel.application.use_cases.configure_socel import (
    ConfigureSocel,
    ConfigureSocelCommand,
)
from ocelescope_module_socel.application.use_cases.get_log_classification import (
    GetLogClassification,
    GetLogClassificationCommand,
)
from ocelescope_module_socel.application.use_cases.socel_changes import (
    RecordsToImport,
    SocelChanges,
)
from ocelescope_module_socel.domain.models.attribute_flows import AttributeFlow, Direction
from ocelescope_module_socel.domain.models.containment import TypeContainment
from ocelescope_module_socel.domain.models.flow_edit import FlowEdit
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
    # The id an uploaded record file is kept under, and which of its columns
    # holds what.
    upload_id: str
    mapping: ColumnMappingModel

    def to_domain(self) -> RecordsToImport:
        return RecordsToImport(upload_id=self.upload_id, mapping=self.mapping.to_domain())


class AttributeFlowModel(ApiModel):
    # An event attribute taken as a flow: each value becomes a record at its
    # event, observed at the event's objects of the type. "out" stores the
    # amounts negative, as the sOCEL marks what flows out of an object; a value
    # that is negative already is taken as it is.
    attribute: str
    flow_id: str
    object_type: str
    direction: Direction = "in"

    def to_domain(self) -> AttributeFlow:
        return AttributeFlow(
            attribute=self.attribute,
            flow_id=self.flow_id,
            object_type=self.object_type,
            direction=self.direction,
        )


class TypeContainmentModel(ApiModel):
    # Objects of object_type lie inside the object of parent_type the
    # object-to-object relation `qualifier` leads them to, for each flow.
    object_type: str
    parent_type: str
    qualifier: str
    flows: list[str]

    def to_domain(self) -> TypeContainment:
        return TypeContainment(
            object_type=self.object_type,
            parent_type=self.parent_type,
            qualifier=self.qualifier,
            flows=tuple(self.flows),
        )


class FlowEditModel(ApiModel):
    # The flow as it is now, and as it is to be.
    flow_id: str
    name: str
    unit: str
    category: str | None
    external_ref: str | None = None
    # Multiplies every record's quantity, for a new unit; null keeps them.
    conversion: float | None = None
    delete: bool = False

    def to_domain(self) -> FlowEdit:
        return FlowEdit(
            flow_id=self.flow_id,
            name=self.name.strip(),
            unit=self.unit.strip(),
            category=self.category,
            external_ref=(self.external_ref or "").strip() or None,
            conversion=self.conversion,
            delete=self.delete,
        )


class SocelChangesModel(ApiModel):
    # Class per activity and per object type; null takes a class away. Types not
    # named keep what they have.
    activities: dict[str, str | None] = Field(default_factory=dict)
    object_types: dict[str, str | None] = Field(default_factory=dict)
    # Unit, category and reference of every flow the changes bring or use; a
    # definition replaces the log's flow of that id.
    flows: dict[str, FlowDefinitionModel] = Field(default_factory=dict)
    records: RecordsToImportModel | None = None
    attribute_flows: list[AttributeFlowModel] = Field(default_factory=list)
    containment: list[TypeContainmentModel] = Field(default_factory=list)
    flow_edits: list[FlowEditModel] = Field(default_factory=list)

    def to_domain(self) -> SocelChanges:
        return SocelChanges(
            activities=self.activities,
            object_types=self.object_types,
            flows={flow_id: flow.to_domain() for flow_id, flow in self.flows.items()},
            records=self.records.to_domain() if self.records else None,
            attribute_flows=tuple(flow.to_domain() for flow in self.attribute_flows),
            containment=tuple(item.to_domain() for item in self.containment),
            flow_edits=tuple(edit.to_domain() for edit in self.flow_edits),
        )


class BuildSocelRequest(SocelChangesModel):
    name: str


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


@router.put(
    "/{ocel_id}/socel",
    operation_id="configureSocel",
    status_code=204,
    responses={422: {"description": "The log cannot be changed as asked."}},
)
def configure_socel(
    ocel_id: str,
    request: SocelChangesModel,
    use_case: Annotated[ConfigureSocel, Depends(get_configure_socel)],
) -> None:
    """Changes the log in place: classifies its events and objects per activity
    and object type, and adds flow records of an uploaded file and of event
    attributes, and containment. The whole log is changed, not only what the
    app's filters show, and it keeps its id and name."""
    use_case.execute(ConfigureSocelCommand(ocel_id=ocel_id, changes=request.to_domain()))


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
    activity and object type, with the flow records of an uploaded file and of
    event attributes."""
    ocel_id = use_case.execute(
        BuildSocelCommand(ocel=ocel, name=request.name, changes=request.to_domain())
    )
    response = BuiltSocelModel(ocel_id=ocel_id)
    return response
