from typing import Annotated

from fastapi import APIRouter, Depends

from ocelescope_module_socel.api.dependencies import get_preview_record_file
from ocelescope_module_socel.application.use_cases.preview_record_file import (
    PreviewRecordFile,
    PreviewRecordFileCommand,
)
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, RecordFilePreview

router = APIRouter()


@router.post(
    "/record-uploads/{upload_id}/preview",
    operation_id="previewRecordFile",
    responses={422: {"description": "The file cannot be read as the mapping says."}},
)
def preview_record_file(
    upload_id: str,
    mapping: ColumnMapping,
    use_case: Annotated[PreviewRecordFile, Depends(get_preview_record_file)],
) -> RecordFilePreview:
    return use_case.execute(PreviewRecordFileCommand(upload_id=upload_id, mapping=mapping))
