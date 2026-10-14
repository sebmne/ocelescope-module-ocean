import math
from collections import Counter
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import field

from ocelescope import OCEL
from socel import DEFAULT_TAXONOMY, SOCEL, SOCELTaxonomies, Taxonomy

from ocelescope_module_socel.application.ports.attribute_flow_importer import (
    AttributeFlowImporter,
)
from ocelescope_module_socel.application.ports.containment_writer import ContainmentWriter
from ocelescope_module_socel.application.ports.flow_editor import FlowEditor
from ocelescope_module_socel.application.ports.log_classifier import LogClassifier
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.application.use_cases.upload_record_file import can_be_read
from ocelescope_module_socel.domain.exceptions import (
    FlowNameTaken,
    InvalidFlowEdit,
    InvalidRecordFile,
    InvalidSocel,
    UndefinedFlow,
    UnknownCategory,
    UnknownClass,
    UnknownFlow,
    UnknownType,
    UnknownUpload,
)
from ocelescope_module_socel.domain.models.attribute_flows import AttributeFlow
from ocelescope_module_socel.domain.models.base import Model
from ocelescope_module_socel.domain.models.containment import TypeContainment
from ocelescope_module_socel.domain.models.flow_edit import FlowEdit
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, FlowDefinition


class RecordsToImport(Model):
    """An uploaded record file and which of its columns holds what."""

    upload_id: str
    mapping: ColumnMapping


class SocelChanges(Model):
    """What a log gets to be or stay an sOCEL: classes, and flows with records."""

    """The class of each activity's events and each object type's objects; None
    takes a class away. Types not named keep what they have."""
    activities: Mapping[str, str | None] = field(default_factory=dict)
    object_types: Mapping[str, str | None] = field(default_factory=dict)
    """Unit, category and reference of every flow the changes bring or use, by
    flow id; a definition replaces the log's flow of that id."""
    flows: Mapping[str, FlowDefinition] = field(default_factory=dict)
    """A file of flow records to add, None for none."""
    records: RecordsToImport | None = None
    """Event attributes to take as flows."""
    attribute_flows: tuple[AttributeFlow, ...] = ()
    """Which objects lie inside which, per flow."""
    containment: tuple[TypeContainment, ...] = ()
    """The log's flows renamed, redefined, converted or deleted; applied before
    anything is added."""
    flow_edits: tuple[FlowEdit, ...] = ()


class ApplySocelChanges:
    """Applies changes to a copy of a log: classifies its events and objects per
    activity and object type, edits the flows it has, adds the flow records of
    an uploaded file and of event attributes, and the containment of flow
    instances. The result must be
    a valid sOCEL; the log itself stays untouched."""

    def __init__(
        self,
        *,
        classifier: LogClassifier,
        importer: RecordImporter,
        attributes: AttributeFlowImporter,
        containment: ContainmentWriter,
        editor: FlowEditor,
        uploads: UploadStore,
        taxonomies: SOCELTaxonomies = DEFAULT_TAXONOMY,
    ) -> None:
        self._editor = editor
        self._classifier = classifier
        self._importer = importer
        self._attributes = attributes
        self._containment = containment
        self._uploads = uploads
        self._taxonomies = taxonomies

    @contextmanager
    def __call__(self, ocel: OCEL, changes: SocelChanges) -> Iterator[OCEL]:
        """The changed copy, checked first and closed when the block ends."""
        current = self._classifier.read(ocel)
        _check_classes(
            "activity",
            changes.activities,
            {activity.name for activity in current.activities},
            self._taxonomies.event_classes,
        )
        _check_classes(
            "object type",
            changes.object_types,
            {object_type.name for object_type in current.object_types},
            self._taxonomies.object_classes,
        )
        self._check_flow_edits(ocel, changes.flow_edits)
        content = self._record_file(ocel, changes)
        for flow in changes.attribute_flows:
            self._check_definition(flow.flow_id, changes)
        for containment in changes.containment:
            for flow_id in containment.flows:
                self._check_definition(flow_id, changes)

        with self._classifier.classify(
            ocel, activities=changes.activities, object_types=changes.object_types
        ) as changed:
            if changes.flow_edits:
                self._editor.edit(changed, changes.flow_edits)
            if changes.records is not None and content is not None:
                self._importer.write(changed, content, changes.records.mapping, changes.flows)
            if changes.attribute_flows:
                self._attributes.write(changed, changes.attribute_flows, changes.flows)
            if changes.containment:
                self._containment.write(changed, changes.containment)
            try:
                SOCEL.from_ocel(changed).close()
            except ValueError as error:
                raise InvalidSocel(str(error)) from error
            yield changed

    def _record_file(self, ocel: OCEL, changes: SocelChanges) -> bytes | None:
        """The uploaded file, once every flow it brings is defined."""
        records = changes.records
        if records is None:
            return None
        content = self._uploads.get(records.upload_id)
        if content is None:
            raise UnknownUpload
        if not can_be_read(records.mapping):
            raise InvalidRecordFile("The columns of the record file are not all assigned.")
        for flow in self._importer.preview(ocel, content, records.mapping).flows:
            if flow.usable_rows > 0:
                self._check_definition(flow.flow_id, changes)
        return content

    def _check_flow_edits(self, ocel: OCEL, edits: tuple[FlowEdit, ...]) -> None:
        if not edits:
            return
        known = self._editor.flow_ids(ocel)
        by_flow = {edit.flow_id: edit for edit in edits}
        if len(by_flow) < len(edits):
            raise InvalidFlowEdit("A flow is changed twice in one go.")
        for edit in edits:
            if edit.flow_id not in known:
                raise UnknownFlow(edit.flow_id)
            if edit.delete:
                continue
            if not edit.name.strip():
                raise InvalidFlowEdit(f"The flow {edit.flow_id!r} needs a name.")
            if not edit.unit.strip():
                raise UndefinedFlow(edit.name)
            if edit.category is not None and edit.category not in self._taxonomies.flow_categories:
                raise UnknownCategory(edit.category)
            if edit.conversion is not None and (
                not math.isfinite(edit.conversion) or edit.conversion == 0
            ):
                raise InvalidFlowEdit(
                    f"The conversion of {edit.flow_id!r} must be a number other than 0."
                )
        names = Counter(
            by_flow[flow_id].name if flow_id in by_flow else flow_id
            for flow_id in known
            if not (flow_id in by_flow and by_flow[flow_id].delete)
        )
        taken = [name for name, count in names.items() if count > 1]
        if taken:
            raise FlowNameTaken(taken[0])

    def _check_definition(self, flow_id: str, changes: SocelChanges) -> None:
        definition = changes.flows.get(flow_id)
        if not flow_id.strip() or definition is None or not definition.unit.strip():
            raise UndefinedFlow(flow_id)
        if definition.category not in self._taxonomies.flow_categories:
            raise UnknownCategory(definition.category)


def _check_classes(
    kind: str, classes: Mapping[str, str | None], known: set[str], taxonomy: Taxonomy
) -> None:
    for name, socel_class in classes.items():
        if name not in known:
            raise UnknownType(kind, name)
        if socel_class is not None and socel_class not in taxonomy:
            raise UnknownClass(kind, socel_class)
