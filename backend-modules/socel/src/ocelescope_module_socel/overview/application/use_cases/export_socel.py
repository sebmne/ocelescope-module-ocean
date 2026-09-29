import tempfile
from dataclasses import dataclass
from pathlib import Path

from ocelescope import OCEL
from socel import SOCEL, SocelValidationError

from ocelescope_module_socel.overview.application.ports.ocel_catalog import OcelCatalog
from ocelescope_module_socel.overview.domain.exceptions import NotAnSocelError, NotConformingError


@dataclass(frozen=True, kw_only=True)
class ExportSocelCommand:
    ocel_id: str


@dataclass(frozen=True, kw_only=True, eq=False)
class ExportedSocel:
    file_name: str
    content: bytes


class ExportSocel:
    """An sOCEL of the user's as its SQLite serialization, as the thesis declares it.

    Ocelescope's own download writes the sOCEL tables without their declarations,
    and empty ones not at all; this one writes them as Appendix A.1 has them.
    Like every export of the thesis' package, it validates first.
    """

    def __init__(self, *, ocel: OCEL, catalog: OcelCatalog) -> None:
        self._ocel = ocel
        self._catalog = catalog

    def execute(self, command: ExportSocelCommand) -> ExportedSocel:
        """Raises:
        NotAnSocelError: The OCEL has no sOCEL tables.
        NotConformingError: The sOCEL does not conform to V1–V9.
        """
        if not SOCEL.is_socel(self._ocel):
            raise NotAnSocelError(f"OCEL {command.ocel_id} has no sOCEL tables.")
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "socel.sqlite"
            try:
                SOCEL(self._ocel).write(path)
            except SocelValidationError as error:
                count = len(error.report.errors)
                errors = f"{count} {'error' if count == 1 else 'errors'}"
                raise NotConformingError(
                    f"The sOCEL does not conform ({errors}); validate it to see where."
                ) from error
            content = path.read_bytes()
        return ExportedSocel(
            file_name=f"{self._catalog.name(command.ocel_id)}.sqlite", content=content
        )
