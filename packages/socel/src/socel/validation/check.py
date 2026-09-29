from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import ClassVar

import polars as pl
from ocelescope import OCEL


class Severity(Enum):
    """ERROR: the log does not conform. WARNING: a quality issue. INFO: worth knowing."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


# eq=False: a frame cannot be compared with ==, so neither can a finding.
@dataclass(frozen=True, eq=False)
class Finding:
    """One problem a check found, with the rows that cause it."""

    check: str
    severity: Severity
    message: str
    rows: pl.DataFrame | None = None


@dataclass(frozen=True)
class Subject:
    """What a validation looks at: the log, and the SQLite file it was read from, if
    any - V1 asks for the file's declarations too."""

    ocel: OCEL
    file: Path | None = None


def counted(n: int, noun: str, plural: str | None = None) -> str:
    """`n` with its noun in the right number: "1 record", "3 records"."""
    return f"{n} {noun if n == 1 else plural or noun + 's'}"


class Check(ABC):
    """One rule. Subclasses name it and implement `run`; a profile runs them in order.

    `requires` names checks this one builds on: if any of them did not pass, this
    one is skipped instead of run, e.g. no overlap check on a missing table.
    """

    id: ClassVar[str]
    title: ClassVar[str]
    severity: ClassVar[Severity] = Severity.ERROR
    requires: ClassVar[tuple[str, ...]] = ()

    @abstractmethod
    def run(self, subject: Subject) -> list[Finding]:
        """The problems found; empty if the rule holds."""

    def finding(self, message: str, rows: pl.DataFrame | None = None) -> Finding:
        return Finding(check=self.id, severity=self.severity, message=message, rows=rows)


class RowCheck(Check):
    """A rule broken by rows: `query` selects exactly the offending ones.

    Most rules have this shape, so they only state the query and how to put a
    result into words.
    """

    @abstractmethod
    def query(self, ocel: OCEL) -> str:
        """SQL selecting the rows that break the rule."""

    @abstractmethod
    def describe(self, rows: pl.DataFrame) -> str:
        """The finding's message, given the offending rows (at least one)."""

    def run(self, subject: Subject) -> list[Finding]:
        rows = subject.ocel.sql(self.query(subject.ocel)).pl()
        return [self.finding(self.describe(rows), rows)] if rows.height else []
