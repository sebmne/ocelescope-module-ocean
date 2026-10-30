from dataclasses import dataclass

from ocelescope_module_socel.application.workflows.open_factor_catalog import OpenFactorCatalog
from ocelescope_module_socel.domain.models.factor_catalog import ResolvedFactor


@dataclass(frozen=True, kw_only=True)
class ResolveCatalogFactorCommand:
    catalog: str
    ref: str
    unit: str


class ResolveCatalogFactor:
    """A catalog factor per one unit of a flow, ready to be used as its factor."""

    def __init__(self, *, open_catalog: OpenFactorCatalog) -> None:
        self._open_catalog = open_catalog

    def execute(self, command: ResolveCatalogFactorCommand) -> ResolvedFactor:
        unit = command.unit.strip()
        if not command.ref or not unit:
            raise ValueError("A factor is resolved by its reference and a unit.")
        return self._open_catalog.open(command.catalog).factor(command.ref, unit=unit)
