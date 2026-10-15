from typing import Annotated

from fastapi import APIRouter, Depends, UploadFile

from ocelescope_module_socel.api.dependencies import get_upload_record_file
from ocelescope_module_socel.application.use_cases.upload_record_file import (
    UploadRecordFile,
    UploadRecordFileCommand,
)
from ocelescope_module_socel.domain.models.record_file import UploadedRecordFile

router = APIRouter()


@router.post(
    "/record-uploads",
    operation_id="uploadRecordFile",
    status_code=201,
    responses={422: {"description": "The file cannot be read as CSV."}},
)
async def upload_record_file(
    file: UploadFile,
    use_case: Annotated[UploadRecordFile, Depends(get_upload_record_file)],
) -> UploadedRecordFile:
    return use_case.execute(UploadRecordFileCommand(content=await file.read()))
