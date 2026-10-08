from collections.abc import Mapping

from ocelescope import OCEL
from socel import DEFAULT_TAXONOMY, SOCEL, SOCELTaxonomies, Taxonomy

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.application.ports.log_classifier import LogClassifier
from ocelescope_module_socel.application.ports.log_store import LogStore
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.domain.exceptions import (
    InvalidSocel,
    UndefinedFlow,
    UnknownCategory,
    UnknownClass,
    UnknownType,
    UnknownUpload,
)
from ocelescope_module_socel.domain.models.base import Model
from ocelescope_module_socel.domain.models.record_file import FlowDefinition


class RecordsToImport(Model):
    """An uploaded record file and the definition of each of its flows."""

    upload_id: str
    flows: Mapping[str, FlowDefinition]


class BuildSocelCommand(Command):
    ocel: OCEL
    """The name the new log is kept under."""
    name: str
    """The class of each activity's events and each object type's objects; None
    takes a class away. Types not named keep what they have."""
    activities: Mapping[str, str | None]
    object_types: Mapping[str, str | None]
    """Flow records to add, None for none."""
    records: RecordsToImport | None = None
    taxonomies: SOCELTaxonomies = DEFAULT_TAXONOMY


class BuildSocel:
    """Turns a log into an sOCEL: a new log with the sOCEL tables, whose events and
    objects are classified per activity and object type and which holds the flow
    records of an uploaded file. Returns the new log's id."""

    def __init__(
        self,
        *,
        classifier: LogClassifier,
        importer: RecordImporter,
        uploads: UploadStore,
        store: LogStore,
    ) -> None:
        self._classifier = classifier
        self._importer = importer
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

        with self._classifier.classify(
            command.ocel, activities=command.activities, object_types=command.object_types
        ) as built:
            if command.records is not None and content is not None:
                self._importer.write(built, content, command.records.flows)
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

        for flow in self._importer.preview(command.ocel, content).flows:
            definition = records.flows.get(flow.flow_id)
            if flow.usable_rows == 0:
                continue
            if definition is None or not definition.unit.strip():
                raise UndefinedFlow(flow.flow_id)
            if definition.category not in command.taxonomies.flow_categories:
                raise UnknownCategory(definition.category)
        return content


def _check_classes(
    kind: str, classes: Mapping[str, str | None], known: set[str], taxonomy: Taxonomy
) -> None:
    for name, socel_class in classes.items():
        if name not in known:
            raise UnknownType(kind, name)
        if socel_class is not None and socel_class not in taxonomy:
            raise UnknownClass(kind, socel_class)
