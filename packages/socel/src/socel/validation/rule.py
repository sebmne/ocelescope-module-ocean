"""Contract implemented by each validation rule."""

from abc import ABC, abstractmethod
from collections.abc import Iterable
from typing import ClassVar

from socel.validation.context import ValidationContext
from socel.validation.issue import ValidationIssue
from socel.validation.result import Invalid, Valid, Validation

type RuleValidation = Validation[None, ValidationIssue]


class ValidationRule(ABC):
    code: ClassVar[str]
    requires: ClassVar[frozenset[str]] = frozenset()

    @abstractmethod
    def validate(self, context: ValidationContext) -> RuleValidation:
        """Return the rule's successful value or all discovered issues."""

    def passed(self) -> RuleValidation:
        return Valid(None)

    def failed(self, *messages: str) -> RuleValidation:
        return Invalid(
            tuple(ValidationIssue(self.code, message) for message in messages)
        )

    def from_messages(self, messages: Iterable[str]) -> RuleValidation:
        issues = tuple(ValidationIssue(self.code, message) for message in messages)
        return Invalid(issues) if issues else Valid(None)
