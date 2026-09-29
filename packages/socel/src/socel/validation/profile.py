from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from ocelescope import OCEL

from socel.validation.check import Check, Severity, Subject
from socel.validation.report import CheckResult, Status, ValidationReport


@dataclass(frozen=True)
class Profile:
    """A named, ordered pipeline of checks: e.g. the thesis' conformance rules V1–V9.

    Profiles combine with `+`, so a project can run the conformance rules plus
    its own checks without changing either.
    """

    name: str
    checks: tuple[Check, ...]

    def __post_init__(self) -> None:
        seen: set[str] = set()
        for check in self.checks:
            if check.id in seen:
                raise ValueError(f"{self.name}: check {check.id} appears twice.")
            later = [required for required in check.requires if required not in seen]
            if later:
                raise ValueError(
                    f"{self.name}: {check.id} requires {', '.join(later)}, "
                    "which must come before it."
                )
            seen.add(check.id)

    def __add__(self, other: Profile) -> Profile:
        return Profile(f"{self.name} + {other.name}", self.checks + other.checks)

    def run(self, ocel: OCEL, file: Path | None = None) -> ValidationReport:
        """Runs the checks in order on the log - and on `file`, the SQLite file it was
        read from, where a check looks at files. A check whose requirements did not
        pass is skipped."""
        subject = Subject(ocel=ocel, file=file)
        results: list[CheckResult] = []
        blocking: set[str] = set()
        for check in self.checks:
            unmet = [required for required in check.requires if required in blocking]
            if unmet:
                result = CheckResult.skipped(check, f"needs {', '.join(unmet)} to pass first")
            else:
                result = CheckResult.of(check, check.run(subject))
            if result.status is Status.SKIPPED or any(
                finding.severity is Severity.ERROR for finding in result.findings
            ):
                blocking.add(check.id)
            results.append(result)
        return ValidationReport(profile=self.name, results=tuple(results))
