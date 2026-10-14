from ocelescope import OCEL

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.application.use_cases.upload_record_file import can_be_read
from ocelescope_module_socel.domain.exceptions import InvalidRecordFile, UnknownUpload
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, RecordFilePreview


class PreviewRecordFileCommand(Command):
    ocel: OCEL
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
        if not can_be_read(command.mapping):
            raise InvalidRecordFile(
                "The file needs a column for the flow, the object and the quantity, "
                "and either for start and end or for the event; or, for end times "
                "only, for the event and the end."
            )
        return self._importer.preview(command.ocel, content, command.mapping)
