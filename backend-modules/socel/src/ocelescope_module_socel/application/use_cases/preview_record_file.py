from dataclasses import dataclass

from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.domain.exceptions import InvalidRecordFile, UnknownUpload
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, RecordFilePreview


@dataclass(frozen=True, kw_only=True)
class PreviewRecordFileCommand:
    upload_id: str
    mapping: ColumnMapping


class PreviewRecordFile:
    """What an uploaded record file holds when its columns are read as the
    mapping says, and which of its rows fit the log."""

    def __init__(self, *, importer: RecordImporter, uploads: UploadStore) -> None:
        self._importer = importer
        self._uploads = uploads

    def execute(self, command: PreviewRecordFileCommand) -> RecordFilePreview:
        content = self._uploads.get(command.upload_id)
        if content is None:
            raise UnknownUpload
        if not command.mapping.is_readable():
            raise InvalidRecordFile(
                "The file needs a column for the flow, the object and the quantity, "
                "and either for start and end or for the event; or, for end times "
                "only, for the event and the end."
            )
        return self._importer.preview(content, command.mapping)
