from typing import Self

from pydantic import Field, model_validator

from ocelescope_module_socel.domain.exceptions import InvalidFlowEdit, InvalidRecordFile
from ocelescope_module_socel.domain.models.attribute_flows import AttributeFlow
from ocelescope_module_socel.domain.models.base import Model
from ocelescope_module_socel.domain.models.containment import TypeContainment
from ocelescope_module_socel.domain.models.flow_edit import FlowEdit
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, FlowDefinition


class RecordsToImport(Model):
    """A session upload and the roles assigned to its columns."""

    upload_id: str
    mapping: ColumnMapping


class PreparationDraft(Model):
    """Requested changes, which may still lack mappings or flow definitions.

    Unnamed types keep their classification; None removes it. Edits happen
    before new records and containment are applied.
    """

    activities: dict[str, str | None] = Field(default_factory=dict)
    object_types: dict[str, str | None] = Field(default_factory=dict)
    flows: dict[str, FlowDefinition] = Field(default_factory=dict)
    records: RecordsToImport | None = None
    attribute_flows: tuple[AttributeFlow, ...] = ()
    containment: tuple[TypeContainment, ...] = ()
    flow_edits: tuple[FlowEdit, ...] = ()


class Preparation(PreparationDraft):
    """An executable change set, produced after validating supplied log facts."""

    @model_validator(mode="after")
    def _executable(self) -> Self:
        if self.records is not None and not self.records.mapping.is_readable():
            raise InvalidRecordFile("The columns of the record file are not all assigned.")
        if len({edit.flow_id for edit in self.flow_edits}) != len(self.flow_edits):
            raise InvalidFlowEdit("A flow is changed twice in one go.")
        return self


class PreparationFacts(Model):
    """Bounded facts needed for preparation, never the complete event graph."""

    activities: frozenset[str]
    object_types: frozenset[str]
    flow_ids: frozenset[str]
