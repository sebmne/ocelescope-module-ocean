from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile
from ocelescope_backend.app.dependencies import ApiOcel

from ocelescope_module_socel.api.dependencies import (
    get_preview_record_file,
    get_upload_record_file,
)
from ocelescope_module_socel.api.schema import ApiModel
from ocelescope_module_socel.application.use_cases.preview_record_file import (
    PreviewRecordFile,
    PreviewRecordFileCommand,
)
from ocelescope_module_socel.application.use_cases.upload_record_file import (
    UploadedRecordFile,
    UploadRecordFile,
    UploadRecordFileCommand,
)
from ocelescope_module_socel.domain.models.record_file import (
    ColumnMapping,
    FlowDefinition,
    FlowInFile,
    IssueKind,
    RecordFilePreview,
    RecordIssue,
    SampleIssue,
)

router = APIRouter(tags=["sOCEL"])


class FlowDefinitionModel(ApiModel):
    unit: str
    category: str
    # Points to the flow in another system, e.g. a database of emission factors.
    external_ref: str | None = None

    @classmethod
    def from_domain(cls, flow: FlowDefinition) -> "FlowDefinitionModel":
        return cls(unit=flow.unit, category=flow.category, external_ref=flow.external_ref)

    def to_domain(self) -> FlowDefinition:
        return FlowDefinition(
            unit=self.unit, category=self.category, external_ref=self.external_ref or None
        )


class FlowInFileModel(ApiModel):
    flow_id: str
    rows: int
    usable_rows: int
    interval_records: int
    event_records: int
    objects: int

    @classmethod
    def from_domain(cls, flow: FlowInFile) -> "FlowInFileModel":
        return cls(
            flow_id=flow.flow_id,
            rows=flow.rows,
            usable_rows=flow.usable_rows,
            interval_records=flow.interval_records,
            event_records=flow.event_records,
            objects=flow.objects,
        )


class RecordIssueModel(ApiModel):
    kind: IssueKind
    rows: int
    # A few of the ids not found in the log, or of the file's line numbers.
    examples: list[str]

    @classmethod
    def from_domain(cls, issue: RecordIssue) -> "RecordIssueModel":
        return cls(kind=issue.kind, rows=issue.rows, examples=list(issue.examples))


class ColumnMappingModel(ApiModel):
    # The name of the file's column that holds each thing; null where the file
    # has none. Flow, object and quantity are needed, and either start and end
    # or the event.
    flow: str | None = None
    object: str | None = None
    quantity: str | None = None
    start_time: str | None = None
    end_time: str | None = None
    event: str | None = None

    @classmethod
    def from_domain(cls, mapping: ColumnMapping) -> "ColumnMappingModel":
        return cls(
            flow=mapping.flow,
            object=mapping.object,
            quantity=mapping.quantity,
            start_time=mapping.start_time,
            end_time=mapping.end_time,
            event=mapping.event,
        )

    def to_domain(self) -> ColumnMapping:
        return ColumnMapping(
            flow=self.flow or None,
            object=self.object or None,
            quantity=self.quantity or None,
            start_time=self.start_time or None,
            end_time=self.end_time or None,
            event=self.event or None,
        )


class SampleIssueModel(ApiModel):
    # A row of the file's first rows (counted from 0) that is left out, and why.
    row: int
    kind: IssueKind

    @classmethod
    def from_domain(cls, issue: SampleIssue) -> "SampleIssueModel":
        return cls(row=issue.row, kind=issue.kind)


class RecordFilePreviewModel(ApiModel):
    rows: int
    usable_rows: int
    # Events the file gives an end time.
    event_ends: int
    flows: list[FlowInFileModel]
    issues: list[RecordIssueModel]
    records_from: datetime | None
    records_to: datetime | None
    sample_issues: list[SampleIssueModel]
    # Whether numbers had a decimal comma and dates the day first.
    decimal_comma: bool
    day_first_dates: bool

    @classmethod
    def from_domain(cls, preview: RecordFilePreview) -> "RecordFilePreviewModel":
        return cls(
            rows=preview.rows,
            usable_rows=preview.usable_rows,
            event_ends=preview.event_ends,
            flows=[FlowInFileModel.from_domain(flow) for flow in preview.flows],
            issues=[RecordIssueModel.from_domain(issue) for issue in preview.issues],
            records_from=preview.records_from,
            records_to=preview.records_to,
            sample_issues=[SampleIssueModel.from_domain(issue) for issue in preview.sample_issues],
            decimal_comma=preview.decimal_comma,
            day_first_dates=preview.day_first_dates,
        )


class UploadedRecordFileModel(ApiModel):
    upload_id: str
    rows: int
    # The character that separates the columns.
    delimiter: str
    # The columns' names, in their order in the file.
    columns: list[str]
    # The first rows as they are: a value per column, null for an empty cell.
    sample: list[list[str | None]]

    @classmethod
    def from_domain(cls, uploaded: UploadedRecordFile) -> "UploadedRecordFileModel":
        return cls(
            upload_id=uploaded.upload_id,
            rows=uploaded.columns.rows,
            delimiter=uploaded.columns.delimiter,
            columns=list(uploaded.columns.columns),
            sample=[list(row) for row in uploaded.columns.sample],
        )


@router.post(
    "/{ocel_id}/flow-records",
    operation_id="uploadRecordFile",
    responses={422: {"description": "The file cannot be read as CSV."}},
)
async def upload_record_file(
    ocel: ApiOcel,
    file: UploadFile,
    use_case: Annotated[UploadRecordFile, Depends(get_upload_record_file)],
) -> UploadedRecordFileModel:
    """Takes a CSV of flow records for the log: says which columns it has and
    shows its first rows, and keeps it for building the sOCEL."""
    result = use_case.execute(UploadRecordFileCommand(ocel=ocel, content=await file.read()))
    response = UploadedRecordFileModel.from_domain(result)
    return response


@router.post(
    "/{ocel_id}/flow-records/{upload_id}/preview",
    operation_id="previewRecordFile",
    responses={422: {"description": "The file cannot be read as the mapping says."}},
)
def preview_record_file(
    ocel: ApiOcel,
    upload_id: str,
    mapping: ColumnMappingModel,
    use_case: Annotated[PreviewRecordFile, Depends(get_preview_record_file)],
) -> RecordFilePreviewModel:
    """What an uploaded file holds when its columns are read as the mapping
    says (a row is an interval record, an event-linked record, or an event's
    end alone), and which rows fit the log. Reads only."""
    result = use_case.execute(
        PreviewRecordFileCommand(ocel=ocel, upload_id=upload_id, mapping=mapping.to_domain())
    )
    response = RecordFilePreviewModel.from_domain(result)
    return response
