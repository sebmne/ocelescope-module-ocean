from contextlib import AbstractContextManager
from typing import Protocol

from ocelescope_module_socel.domain.models.preparation import Preparation, PreparationFacts
from ocelescope_module_socel.domain.models.record_file import ColumnMapping, RecordFilePreview


class SocelWork(Protocol):
    """A disposable working copy; publish only after conformance validation."""

    def facts(self) -> PreparationFacts: ...

    def preview(self, content: bytes, mapping: ColumnMapping) -> RecordFilePreview: ...

    def apply(self, preparation: Preparation, record_content: bytes | None) -> None:
        """Apply edits before importing records, attributes, and containment."""
        ...

    def validate(self) -> None: ...

    def publish_new(self, name: str) -> str: ...

    def publish_replacing(self) -> None: ...


class SocelWorkspace(Protocol):
    def open(self) -> AbstractContextManager[SocelWork]:
        """Borrow the bound source and close all created resources on exit."""
        ...
