"""Validation exceptions exposed by the library."""

from collections.abc import Sequence

from socel.validation.issue import ValidationIssue


class SOCELValidationError(ValueError):
    """An OCEL failed one or more sOCEL conformance rules."""

    def __init__(self, issues: Sequence[ValidationIssue]) -> None:
        self.issues = tuple(issues)
        self.messages = tuple(str(issue) for issue in self.issues)
        details = "\n".join(f"- {message}" for message in self.messages)
        super().__init__(f"Invalid sOCEL:\n{details}")
