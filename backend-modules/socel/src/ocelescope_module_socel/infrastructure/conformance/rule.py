"""Contract implemented by each validation rule."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import ClassVar

from ocelescope_module_socel.infrastructure.conformance.context import ValidationContext
from ocelescope_module_socel.infrastructure.conformance.issue import ValidationIssue
from ocelescope_module_socel.infrastructure.conformance.result import Invalid, Valid, Validation


class ValidationRule(ABC):
    code: ClassVar[str]
    requires: ClassVar[frozenset[str]] = frozenset()

    @abstractmethod
    def validate(self, context: ValidationContext) -> Validation:
        """Return success or all discovered issues."""

    def passed(self) -> Validation:
        return Valid()

    def failed(self, *messages: str) -> Validation:
        return Invalid(tuple(ValidationIssue(self.code, message) for message in messages))

    def from_messages(self, messages: Iterable[str]) -> Validation:
        issues = tuple(ValidationIssue(self.code, message) for message in messages)
        return Invalid(issues) if issues else Valid()
