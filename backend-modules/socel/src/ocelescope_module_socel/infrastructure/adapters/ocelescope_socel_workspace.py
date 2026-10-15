from collections.abc import Iterator
from contextlib import ExitStack, contextmanager
from copy import deepcopy

from ocelescope import OCEL
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_socel.domain.exceptions import InvalidSocel
from ocelescope_module_socel.domain.models.preparation import Preparation, PreparationFacts
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, RecordFilePreview
from ocelescope_module_socel.infrastructure.adapters.duckdb_attribute_flow_importer import (
    DuckDbAttributeFlowImporter,
)
from ocelescope_module_socel.infrastructure.adapters.duckdb_containment_writer import (
    DuckDbContainmentWriter,
)
from ocelescope_module_socel.infrastructure.adapters.duckdb_flow_editor import DuckDbFlowEditor
from ocelescope_module_socel.infrastructure.adapters.duckdb_log_classifier import (
    DuckDbLogClassifier,
)
from ocelescope_module_socel.infrastructure.adapters.duckdb_record_importer import (
    DuckDbRecordImporter,
)
from ocelescope_module_socel.infrastructure.adapters.ocelescope_log_store import OcelescopeLogStore
from ocelescope_module_socel.infrastructure.ocelescope_extension import SOCEL


class OcelescopeSocelWorkspace:
    """Borrow a host log and lazily own one disposable copy for preparation."""

    def __init__(self, session: Session, source: OCEL, *, ocel_id: str | None = None) -> None:
        self._store = OcelescopeLogStore(session)
        self._source = source
        self._ocel_id = ocel_id

    @contextmanager
    def open(self) -> Iterator["_SocelWork"]:
        with ExitStack() as resources:
            yield _SocelWork(self._source, self._store, self._ocel_id, resources)


class _SocelWork:
    def __init__(
        self, source: OCEL, store: OcelescopeLogStore, ocel_id: str | None, resources: ExitStack
    ) -> None:
        self._source = source
        self._store = store
        self._ocel_id = ocel_id
        self._resources = resources
        self._changed: OCEL | None = None
        self._applied = False
        self._validated = False
        self._published = False

    def facts(self) -> PreparationFacts:
        current = DuckDbLogClassifier(self._source).read()
        return PreparationFacts(
            activities=frozenset(item.name for item in current.activities),
            object_types=frozenset(item.name for item in current.object_types),
            flow_ids=frozenset(DuckDbFlowEditor().flow_ids(self._source)),
        )

    def preview(self, content: bytes, mapping: ColumnMapping) -> RecordFilePreview:
        return DuckDbRecordImporter(self._source).preview(content, mapping)

    def apply(self, preparation: Preparation, record_content: bytes | None) -> None:
        if self._changed is not None:
            raise RuntimeError("A workspace can apply one preparation only.")
        changed = self._resources.enter_context(deepcopy(self._source))
        self._changed = changed
        DuckDbLogClassifier(changed).classify(
            activities=preparation.activities, object_types=preparation.object_types
        )
        if preparation.flow_edits:
            DuckDbFlowEditor().edit(changed, preparation.flow_edits)
        if preparation.records is not None:
            if record_content is None:
                raise RuntimeError("The prepared record upload has no content.")
            DuckDbRecordImporter(changed).write(
                record_content, preparation.records.mapping, preparation.flows
            )
        if preparation.attribute_flows:
            DuckDbAttributeFlowImporter().write(
                changed, preparation.attribute_flows, preparation.flows
            )
        if preparation.containment:
            DuckDbContainmentWriter().write(changed, preparation.containment)
        self._applied = True

    def validate(self) -> None:
        if not self._applied or self._changed is None:
            raise RuntimeError("Apply a preparation successfully before validating the workspace.")
        try:
            SOCEL.from_ocel(self._changed).close()
        except ValueError as error:
            raise InvalidSocel(str(error)) from error
        self._validated = True

    def _ready(self) -> OCEL:
        if not self._validated or self._changed is None:
            raise RuntimeError("Validate the working copy before publishing it.")
        if self._published:
            raise RuntimeError("The working copy has already been published.")
        return self._changed

    def publish_new(self, name: str) -> str:
        result = self._store.add(self._ready(), name)
        self._published = True
        return result

    def publish_replacing(self) -> None:
        if self._ocel_id is None:
            raise RuntimeError("This workspace has no log to replace.")
        self._store.replace(self._ocel_id, self._ready())
        self._published = True
