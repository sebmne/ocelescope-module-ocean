from dataclasses import dataclass

from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.domain.models.record_file import UploadedRecordFile


@dataclass(frozen=True, kw_only=True)
class UploadRecordFileCommand:
    content: bytes


class UploadRecordFile:
    def __init__(self, *, importer: RecordImporter, uploads: UploadStore) -> None:
        self._importer = importer
        self._uploads = uploads

    def execute(self, command: UploadRecordFileCommand) -> UploadedRecordFile:
        columns = self._importer.columns(command.content)
        return UploadedRecordFile(
            upload_id=self._uploads.put(command.content), **columns.model_dump(by_alias=False)
        )
