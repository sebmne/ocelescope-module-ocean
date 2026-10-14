from collections.abc import Mapping
from dataclasses import field

from ocelescope import OCEL
from socel import DEFAULT_TAXONOMY, SOCEL, SOCELTaxonomies, Taxonomy

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.attribute_flow_importer import (
    AttributeFlowImporter,
)
from ocelescope_module_socel.application.ports.containment_writer import ContainmentWriter
from ocelescope_module_socel.application.ports.log_classifier import LogClassifier
from ocelescope_module_socel.application.ports.log_store import LogStore
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.application.use_cases.upload_record_file import can_be_read
from ocelescope_module_socel.domain.exceptions import (
    InvalidRecordFile,
    InvalidSocel,
    UndefinedFlow,
    UnknownCategory,
    UnknownClass,
    UnknownType,
    UnknownUpload,
)
from ocelescope_module_socel.domain.models.attribute_flows import AttributeFlow
from ocelescope_module_socel.domain.models.base import Model
from ocelescope_module_socel.domain.models.containment import TypeContainment
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, FlowDefinition


class RecordsToImport(Model):
    """An uploaded record file and which of its columns holds what."""

    upload_id: str
    mapping: ColumnMapping


class BuildSocelCommand(Command):
    ocel: OCEL
    """The name the new log is kept under."""
    name: str
    """The class of each activity's events and each object type's objects; None
    takes a class away. Types not named keep what they have."""
    activities: Mapping[str, str | None]
    object_types: Mapping[str, str | None]
    """Unit, category and reference of every flow the build brings, by flow id."""
    flows: Mapping[str, FlowDefinition] = field(default_factory=dict)
    """A file of flow records to add, None for none."""
    records: RecordsToImport | None = None
    """Event attributes to take as flows."""
    attribute_flows: tuple[AttributeFlow, ...] = ()
    """Which objects lie inside which, per flow."""
    containment: tuple[TypeContainment, ...] = ()
    taxonomies: SOCELTaxonomies = DEFAULT_TAXONOMY


class BuildSocel:
    """Turns a log into an sOCEL: a new log with the sOCEL tables, whose events and
    objects are classified per activity and object type and which holds the flow
    records of an uploaded file and of event attributes, and the containment of
    its flow instances. Returns the new log's id."""

    def __init__(
        self,
        *,
        classifier: LogClassifier,
        importer: RecordImporter,
        attributes: AttributeFlowImporter,
        containment: ContainmentWriter,
        uploads: UploadStore,
        store: LogStore,
    ) -> None:
        self._classifier = classifier
        self._importer = importer
        self._attributes = attributes
        self._containment = containment
        self._uploads = uploads
        self._store = store

    def execute(self, command: BuildSocelCommand) -> str:
        current = self._classifier.read(command.ocel)
        _check_classes(
            "activity",
            command.activities,
            {activity.name for activity in current.activities},
            command.taxonomies.event_classes,
        )
        _check_classes(
            "object type",
            command.object_types,
            {object_type.name for object_type in current.object_types},
            command.taxonomies.object_classes,
        )
        content = self._record_file(command)
        self._check_attribute_flows(command)

        with self._classifier.classify(
            command.ocel, activities=command.activities, object_types=command.object_types
        ) as built:
            if command.records is not None and content is not None:
                self._importer.write(built, content, command.records.mapping, command.flows)
            if command.attribute_flows:
                self._attributes.write(built, command.attribute_flows, command.flows)
            if command.containment:
                self._containment.write(built, command.containment)
            try:
                SOCEL.from_ocel(built).close()
            except ValueError as error:
                raise InvalidSocel(str(error)) from error
            return self._store.add(built, command.name)

    def _record_file(self, command: BuildSocelCommand) -> bytes | None:
        """The uploaded file, once every flow it brings is defined."""
        records = command.records
        if records is None:
            return None
        content = self._uploads.get(records.upload_id)
        if content is None:
            raise UnknownUpload
        if not can_be_read(records.mapping):
            raise InvalidRecordFile("The columns of the record file are not all assigned.")

        for flow in self._importer.preview(command.ocel, content, records.mapping).flows:
            if flow.usable_rows > 0:
                _check_definition(flow.flow_id, command)
        return content

    def _check_attribute_flows(self, command: BuildSocelCommand) -> None:
        """The flow of every attribute and every containment is defined."""
        for flow in command.attribute_flows:
            _check_definition(flow.flow_id, command)
        for containment in command.containment:
            for flow_id in containment.flows:
                _check_definition(flow_id, command)


def _check_definition(flow_id: str, command: BuildSocelCommand) -> None:
    definition = command.flows.get(flow_id)
    if not flow_id.strip() or definition is None or not definition.unit.strip():
        raise UndefinedFlow(flow_id)
    if definition.category not in command.taxonomies.flow_categories:
        raise UnknownCategory(definition.category)


def _check_classes(
    kind: str, classes: Mapping[str, str | None], known: set[str], taxonomy: Taxonomy
) -> None:
    for name, socel_class in classes.items():
        if name not in known:
            raise UnknownType(kind, name)
        if socel_class is not None and socel_class not in taxonomy:
            raise UnknownClass(kind, socel_class)
