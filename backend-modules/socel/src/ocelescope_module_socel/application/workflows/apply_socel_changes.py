from ocelescope_module_socel.application.ports.socel_workspace import SocelWork
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.domain.exceptions import InvalidRecordFile, UnknownUpload
from ocelescope_module_socel.domain.models.preparation import PreparationDraft
from ocelescope_module_socel.domain.services.preparation_validator import PreparationValidator


class ApplySocelChanges:
    """Internal coordination shared by build and configure; no business rules."""

    def __init__(self, *, uploads: UploadStore, validator: PreparationValidator) -> None:
        self._uploads = uploads
        self._validator = validator

    def apply(self, work: SocelWork, draft: PreparationDraft) -> None:
        content = None
        record_flows: tuple[str, ...] = ()
        if draft.records is not None:
            content = self._uploads.get(draft.records.upload_id)
            if content is None:
                raise UnknownUpload
            if not draft.records.mapping.is_readable():
                raise InvalidRecordFile("The columns of the record file are not all assigned.")
            preview = work.preview(content, draft.records.mapping)
            record_flows = tuple(flow.flow_id for flow in preview.flows if flow.usable_rows > 0)
        preparation = self._validator.prepare(draft, work.facts(), record_flows=record_flows)
        work.apply(preparation, content)
        work.validate()
