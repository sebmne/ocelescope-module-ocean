"""Explicit success and error accumulation at the conformance boundary."""

import pytest

from ocelescope_module_socel.infrastructure.conformance.error import SocelValidationError
from ocelescope_module_socel.infrastructure.conformance.issue import ValidationIssue
from ocelescope_module_socel.infrastructure.conformance.result import Invalid, Valid, combine


def test_combine_accumulates_independent_issues_in_order() -> None:
    first = ValidationIssue("V1", "first")
    second = ValidationIssue("V2", "second")
    third = ValidationIssue("V2", "third")

    result = combine((Invalid((first,)), Valid(), Invalid((second, third))))

    assert result == Invalid((first, second, third))


def test_combine_all_passed_checks_returns_fieldless_success() -> None:
    assert combine((Valid(), Valid())) == Valid()


def test_combine_no_checks_is_valid() -> None:
    assert combine(()) == Valid()


def test_invalid_results_require_an_issue() -> None:
    with pytest.raises(ValueError, match="at least one error"):
        Invalid(())


def test_invalid_result_raises_the_supplied_exception_with_all_issues() -> None:
    issues = (ValidationIssue("V1", "first"), ValidationIssue("V2", "second"))

    with pytest.raises(SocelValidationError) as raised:
        Invalid(issues).unwrap_or_raise(SocelValidationError)

    assert raised.value.issues == issues
    assert raised.value.messages == ("[V1] first", "[V2] second")


def test_valid_result_does_not_construct_an_exception() -> None:
    def unexpected_exception(issues: tuple[ValidationIssue, ...]) -> Exception:
        raise AssertionError("A successful validation must not construct an exception.")

    Valid().unwrap_or_raise(unexpected_exception)
