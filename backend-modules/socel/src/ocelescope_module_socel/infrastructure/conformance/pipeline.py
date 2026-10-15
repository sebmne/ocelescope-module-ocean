"""Execution of an ordered set of validation rules."""

from dataclasses import dataclass

from ocelescope import OCEL

from ocelescope_module_socel.infrastructure.conformance.context import ValidationContext
from ocelescope_module_socel.infrastructure.conformance.queries import inspect_columns
from ocelescope_module_socel.infrastructure.conformance.result import Invalid, Validation, combine
from ocelescope_module_socel.infrastructure.conformance.rule import ValidationRule


@dataclass(frozen=True)
class ValidationPipeline:
    rules: list[ValidationRule]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for rule in self.rules:
            if rule.code in seen:
                raise ValueError(f"Validation rule {rule.code} occurs more than once.")

            dependencies_after_rule = rule.requires - seen
            if dependencies_after_rule:
                dependencies = ", ".join(sorted(dependencies_after_rule))
                raise ValueError(
                    f"Rule {rule.code} must run after its dependencies: {dependencies}."
                )
            seen.add(rule.code)

    def validate(self, ocel: OCEL) -> Validation:
        """Evaluate every rule whose dependencies passed."""
        context = ValidationContext(
            ocel=ocel,
            columns=inspect_columns(ocel),
        )
        unavailable: set[str] = set()
        results: list[Validation] = []

        for rule in self.rules:
            if rule.requires & unavailable:
                unavailable.add(rule.code)
                continue

            result = rule.validate(context)
            results.append(result)
            if isinstance(result, Invalid):
                unavailable.add(rule.code)

        return combine(results)
