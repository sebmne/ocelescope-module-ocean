"""Validating an sOCEL: profiles are ordered pipelines of checks.

The conformance profile holds the thesis' rules V1–V9 and decides whether a log
is an sOCEL. Taxonomy and signature checks, which only ever warn or inform, get
profiles of their own.
"""

from socel.validation.check import Check, Finding, RowCheck, Severity, Subject
from socel.validation.conformance import CONFORMANCE
from socel.validation.profile import Profile
from socel.validation.report import (
    CheckResult,
    SocelValidationError,
    Status,
    ValidationReport,
)

__all__ = [
    "CONFORMANCE",
    "Check",
    "CheckResult",
    "Finding",
    "Profile",
    "RowCheck",
    "Severity",
    "SocelValidationError",
    "Status",
    "Subject",
    "ValidationReport",
]
