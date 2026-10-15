"""A small validation type for composing fallible checks."""

from collections.abc import Callable, Iterable
from dataclasses import dataclass

from ocelescope_module_socel.infrastructure.conformance.issue import ValidationIssue


@dataclass(frozen=True, slots=True)
class Valid:
    """A successful validation, with no payload."""

    def unwrap_or_raise(
        self, exception: Callable[[tuple[ValidationIssue, ...]], Exception]
    ) -> None:
        """Return normally at an exception-based validation boundary."""


@dataclass(frozen=True, slots=True)
class Invalid:
    """A failed validation containing every discovered error."""

    errors: tuple[ValidationIssue, ...]

    def __post_init__(self) -> None:
        if not self.errors:
            raise ValueError("An invalid result must contain at least one error.")

    def unwrap_or_raise(
        self, exception: Callable[[tuple[ValidationIssue, ...]], Exception]
    ) -> None:
        raise exception(self.errors)


type Validation = Valid | Invalid


def combine(validations: Iterable[Validation]) -> Validation:
    """Combine independent validations, accumulating all of their errors."""
    errors = tuple(
        issue
        for validation in validations
        if isinstance(validation, Invalid)
        for issue in validation.errors
    )
    return Invalid(errors) if errors else Valid()
