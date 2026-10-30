from ocelescope_module_socel.application.errors import UnknownFactorCatalog
from ocelescope_module_socel.application.ports.factor_catalog import CatalogOffer, FactorCatalog
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.climatiq import (
    ClimatiqConnector,
)

# The catalogs on offer, in the order they are shown. A new one is offered here
# and created in `create`.
_OFFERS = (CatalogOffer("climatiq", "Climatiq"),)


class ExternalFactorCatalogFactory:
    """Creates the external factor catalogs the module offers."""

    def __init__(self, *, climatiq_data_version: str | None = None) -> None:
        self._climatiq = ClimatiqConnector(data_version=climatiq_data_version)

    def offered(self) -> tuple[CatalogOffer, ...]:
        return _OFFERS

    def offer(self, catalog: str) -> CatalogOffer:
        found = next((offer for offer in _OFFERS if offer.id == catalog), None)
        if found is None:
            raise UnknownFactorCatalog(catalog)
        return found

    def create(self, catalog: str, key: str) -> FactorCatalog:
        match catalog:
            case "climatiq":
                return self._climatiq.connect(key)
            case _:
                raise UnknownFactorCatalog(catalog)
