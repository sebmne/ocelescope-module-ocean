from dataclasses import dataclass

from ocelescope_module_socel.application.ports.factor_catalog import FactorSlice
from ocelescope_module_socel.application.workflows.open_factor_catalog import OpenFactorCatalog
from ocelescope_module_socel.domain.models.factor_catalog import FactorQuery


@dataclass(frozen=True, kw_only=True)
class SearchFactorCatalogCommand:
    catalog: str
    text: str
    offset: int
    limit: int
    unit: str | None = None
    region: str | None = None
    year: int | None = None


class SearchFactorCatalog:
    def __init__(self, *, open_catalog: OpenFactorCatalog) -> None:
        self._open_catalog = open_catalog

    def execute(self, command: SearchFactorCatalogCommand) -> FactorSlice:
        if command.offset < 0 or command.limit < 1:
            raise ValueError("Offset must be nonnegative and limit must be positive.")
        text = command.text.strip()
        if not text:
            raise ValueError("A search needs some text.")
        query = FactorQuery(
            text=text,
            unit=_blank_to_none(command.unit),
            region=_blank_to_none(command.region),
            year=command.year,
        )
        catalog = self._open_catalog.open(command.catalog)
        return catalog.search(query, offset=command.offset, limit=command.limit)


def _blank_to_none(value: str | None) -> str | None:
    return value.strip() or None if value is not None else None
