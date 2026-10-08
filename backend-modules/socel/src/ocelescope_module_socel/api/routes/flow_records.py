from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from ocelescope_backend.app.dependencies import ApiOcel

from ocelescope_module_socel.api.dependencies import get_upload_record_file
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.upload_record_file import (
    UploadedRecordFile,
    UploadRecordFile,
    UploadRecordFileCommand,
)
from ocelescope_module_socel.domain.models.record_file import (
    FlowDefinition,
    FlowInFile,
    IssueKind,
    RecordIssue,
)

router = APIRouter(tags=["sOCEL"])


class FlowDefinitionModel(ApiModel):
    unit: str
    category: str

    @classmethod
    def from_domain(cls, flow: FlowDefinition) -> "FlowDefinitionModel":
        return cls(unit=flow.unit, category=flow.category)

    def to_domain(self) -> FlowDefinition:
        return FlowDefinition(unit=self.unit, category=self.category)


class FlowInFileModel(ApiModel):
    flow_id: str
    rows: int
    usable_rows: int
    interval_records: int
    event_records: int
    objects: int
    # The flow's definition when the log already has the flow.
    # The flow's definition when the log already has the flow.
    known: FlowDefinitionModel | None

    @classmethod
    def from_domain(cls, flow: FlowInFile) -> "FlowInFileModel":
        return cls(
            flow_id=flow.flow_id,
            rows=flow.rows,
            usable_rows=flow.usable_rows,
            interval_records=flow.interval_records,
            event_records=flow.event_records,
            objects=flow.objects,
            known=FlowDefinitionModel.from_domain(flow.known) if flow.known else None,
        )


class RecordIssueModel(ApiModel):
    kind: IssueKind
    rows: int
    # A few of the ids not found in the log, or of the file's line numbers.
    examples: list[str]

    @classmethod
    def from_domain(cls, issue: RecordIssue) -> "RecordIssueModel":
        return cls(kind=issue.kind, rows=issue.rows, examples=list(issue.examples))


class UploadedRecordFileModel(ApiModel):
    upload_id: str
    rows: int
    usable_rows: int
    flows: list[FlowInFileModel]
    issues: list[RecordIssueModel]
    records_from: datetime | None
    records_to: datetime | None

    @classmethod
    def from_domain(cls, uploaded: UploadedRecordFile) -> "UploadedRecordFileModel":
        preview = uploaded.preview
        return cls(
            upload_id=uploaded.upload_id,
            rows=preview.rows,
            usable_rows=preview.usable_rows,
            flows=[FlowInFileModel.from_domain(flow) for flow in preview.flows],
            issues=[RecordIssueModel.from_domain(issue) for issue in preview.issues],
            records_from=preview.records_from,
            records_to=preview.records_to,
        )


@router.post(
    "/{ocel_id}/flow-records",
    operation_id="uploadRecordFile",
    responses={422: {"description": "The file is no record file."}},
)
async def upload_record_file(
    ocel: ApiOcel,
    file: UploadFile,
    use_case: Annotated[UploadRecordFile, Depends(get_upload_record_file)],
) -> UploadedRecordFileModel:
    """Takes a CSV of flow records for the log (columns flow, object, quantity,
    and either start_time and end_time or event): says what it holds and which
    rows fit the log, and keeps it for building the sOCEL."""
    result = use_case.execute(UploadRecordFileCommand(ocel=ocel, content=await file.read()))
    response = UploadedRecordFileModel.from_domain(result)
    return response
