from dataclasses import dataclass

from ocelescope import OCEL
from socel import SOCEL, ValidationReport

from ocelescope_module_socel.overview.domain.exceptions import NotAnSocelError


@dataclass(frozen=True, kw_only=True)
class ValidateSocelCommand:
    ocel_id: str


@dataclass(frozen=True, kw_only=True, eq=False)
class ValidationResult:
    report: ValidationReport


class ValidateSocel:
    """Checks an OCEL of the user's against V1–V9."""

    def __init__(self, *, ocel: OCEL) -> None:
        self._ocel = ocel

    def execute(self, command: ValidateSocelCommand) -> ValidationResult:
        """Raises:
        NotAnSocelError: The OCEL has no sOCEL tables.
        """
        if not SOCEL.is_socel(self._ocel):
            raise NotAnSocelError(f"OCEL {command.ocel_id} has no sOCEL tables.")
        return ValidationResult(report=SOCEL(self._ocel).validate())
