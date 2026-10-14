from ocelescope import OCEL

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.domain.models.base import Model
from ocelescope_module_socel.domain.models.record_file import (
    ColumnMapping,
    RecordFileColumns,
)


class UploadRecordFileCommand(Command):
    ocel: OCEL
    content: bytes


class UploadedRecordFile(Model):
    """The id the file is kept under, its columns and its first rows."""

    upload_id: str
    columns: RecordFileColumns


class UploadRecordFile:
    """Takes a record file for a log: says which columns it has and shows its
    first rows, and keeps it for building the sOCEL. What each column holds is
    for the user to say."""

    def __init__(self, *, importer: RecordImporter, uploads: UploadStore) -> None:
        self._importer = importer
        self._uploads = uploads

    def execute(self, command: UploadRecordFileCommand) -> UploadedRecordFile:
        columns = self._importer.columns(command.ocel, command.content)
        return UploadedRecordFile(upload_id=self._uploads.put(command.content), columns=columns)


def can_be_read(mapping: ColumnMapping) -> bool:
    """Whether the mapping names enough columns: for records flow, object and
    quantity, and either start and end or the event; for the end times of
    events alone the event and the end."""
    records = None not in (mapping.flow, mapping.object, mapping.quantity) and (
        mapping.event is not None or None not in (mapping.start_time, mapping.end_time)
    )
    event_ends = None not in (mapping.event, mapping.end_time)
    return records or event_ends
