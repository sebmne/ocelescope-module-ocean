"""Validation at the OCEL-to-sOCEL type boundary."""

from ocelescope_module_socel.infrastructure.conformance.error import SocelValidationError
from ocelescope_module_socel.infrastructure.conformance.issue import ValidationIssue
from ocelescope_module_socel.infrastructure.conformance.pipeline import ValidationPipeline
from ocelescope_module_socel.infrastructure.conformance.result import (
    Invalid,
    Valid,
    Validation,
    combine,
)

__all__ = [
    "Invalid",
    "SocelValidationError",
    "Valid",
    "Validation",
    "ValidationIssue",
    "ValidationPipeline",
    "combine",
]
