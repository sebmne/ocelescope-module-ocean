"""A small validation type for composing fallible checks."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Valid[T, E]:
    """A successful validation."""

    value: T

    def map[U](self, function: Callable[[T], U]) -> Validation[U, E]:
        return Valid(function(self.value))

    def and_then[U](
        self, function: Callable[[T], Validation[U, E]]
    ) -> Validation[U, E]:
        return function(self.value)

    def unwrap_or_raise(self, exception: Callable[[tuple[E, ...]], Exception]) -> T:
        return self.value


@dataclass(frozen=True, slots=True)
class Invalid[T, E]:
    """A failed validation containing every discovered error."""

    errors: tuple[E, ...]

    def __post_init__(self) -> None:
        if not self.errors:
            raise ValueError("An invalid result must contain at least one error.")

    def map[U](self, function: Callable[[T], U]) -> Validation[U, E]:
        return Invalid(self.errors)

    def and_then[U](
        self, function: Callable[[T], Validation[U, E]]
    ) -> Validation[U, E]:
        return Invalid(self.errors)

    def unwrap_or_raise(self, exception: Callable[[tuple[E, ...]], Exception]) -> T:
        raise exception(self.errors)


type Validation[T, E] = Valid[T, E] | Invalid[T, E]


def combine[T, E](
    validations: Iterable[Validation[T, E]],
) -> Validation[tuple[T, ...], E]:
    """Combine independent validations, accumulating all of their errors."""
    values: list[T] = []
    errors: list[E] = []

    for validation in validations:
        match validation:
            case Valid(value):
                values.append(value)
            case Invalid(validation_errors):
                errors.extend(validation_errors)

    if errors:
        return Invalid(tuple(errors))
    return Valid(tuple(values))
