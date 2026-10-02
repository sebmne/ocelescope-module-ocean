"""Structured errors produced by sOCEL validation rules."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    rule: str
    message: str

    def __str__(self) -> str:
        return f"[{self.rule}] {self.message}"
