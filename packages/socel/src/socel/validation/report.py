from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from socel.errors import SocelError
from socel.validation.check import Check, Finding, Severity


class Status(Enum):
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass(frozen=True, eq=False)
class CheckResult:
    """What one check of a profile came to."""

    check: Check
    status: Status
    findings: tuple[Finding, ...] = ()
    # Why the check was skipped.
    reason: str | None = None

    @classmethod
    def of(cls, check: Check, findings: list[Finding]) -> CheckResult:
        return cls(check, Status.FAILED if findings else Status.PASSED, tuple(findings))

    @classmethod
    def skipped(cls, check: Check, reason: str) -> CheckResult:
        return cls(check, Status.SKIPPED, reason=reason)


@dataclass(frozen=True, eq=False)
class ValidationReport:
    """The results of a profile's checks, in their order."""

    profile: str
    results: tuple[CheckResult, ...]

    def __getitem__(self, check_id: str) -> CheckResult:
        for result in self.results:
            if result.check.id == check_id:
                return result
        raise KeyError(check_id)

    @property
    def findings(self) -> tuple[Finding, ...]:
        return tuple(finding for result in self.results for finding in result.findings)

    @property
    def errors(self) -> tuple[Finding, ...]:
        return self._with(Severity.ERROR)

    @property
    def warnings(self) -> tuple[Finding, ...]:
        return self._with(Severity.WARNING)

    @property
    def infos(self) -> tuple[Finding, ...]:
        return self._with(Severity.INFO)

    @property
    def is_conforming(self) -> bool:
        """No errors, and no rule that could decide it left unchecked."""
        unchecked = any(
            result.status is Status.SKIPPED and result.check.severity is Severity.ERROR
            for result in self.results
        )
        return not self.errors and not unchecked

    def __str__(self) -> str:
        marks = {Status.PASSED: "✔", Status.FAILED: "✘", Status.SKIPPED: "–"}
        lines = [f"{self.profile}: {'conforming' if self.is_conforming else 'not conforming'}"]
        for result in self.results:
            lines.append(f"  {marks[result.status]} {result.check.id}  {result.check.title}")
            if result.reason:
                lines.append(f"       skipped: {result.reason}")
            lines.extend(
                f"       {finding.severity.value}: {finding.message}" for finding in result.findings
            )
        return "\n".join(lines)

    def _with(self, severity: Severity) -> tuple[Finding, ...]:
        return tuple(finding for finding in self.findings if finding.severity is severity)


class SocelValidationError(SocelError):
    """An sOCEL does not conform to the thesis' conditions V1–V9.

    Raised when reading, writing or building one; `report` says where.
    """

    def __init__(self, report: ValidationReport) -> None:
        self.report = report
        errors = len(report.errors)
        super().__init__(
            f"Not a conforming sOCEL ({errors} {'error' if errors == 1 else 'errors'}).\n{report}"
        )
