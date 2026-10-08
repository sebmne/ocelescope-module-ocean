from ocelescope import OCEL

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.domain.models.base import Model
from ocelescope_module_socel.domain.models.record_file import RecordFilePreview


class UploadRecordFileCommand(Command):
    ocel: OCEL
    content: bytes


class UploadedRecordFile(Model):
    """The id the file is kept under, and what it holds."""

    upload_id: str
    preview: RecordFilePreview


class UploadRecordFile:
    """Takes a record file for a log: says what it holds and which of its rows fit
    the log, and keeps it for building the sOCEL."""

    def __init__(self, *, importer: RecordImporter, uploads: UploadStore) -> None:
        self._importer = importer
        self._uploads = uploads

    def execute(self, command: UploadRecordFileCommand) -> UploadedRecordFile:
        preview = self._importer.preview(command.ocel, command.content)
        return UploadedRecordFile(upload_id=self._uploads.put(command.content), preview=preview)
