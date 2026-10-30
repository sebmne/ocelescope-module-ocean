from ocelescope_module_socel.application.errors import FactorCatalogNotConnected
from ocelescope_module_socel.application.ports.catalog_credentials import CatalogCredentials
from ocelescope_module_socel.application.ports.factor_catalog import (
    FactorCatalog,
    FactorCatalogFactory,
)


class OpenFactorCatalog:
    """Internal coordination shared by search and resolve: a catalog, opened
    with the key kept for it; no business rules."""

    def __init__(self, *, factory: FactorCatalogFactory, credentials: CatalogCredentials) -> None:
        self._factory = factory
        self._credentials = credentials

    def open(self, catalog: str) -> FactorCatalog:
        """Raises UnknownFactorCatalog, or FactorCatalogNotConnected without a key."""
        offer = self._factory.offer(catalog)
        key = self._credentials.key(catalog)
        if key is None:
            raise FactorCatalogNotConnected(offer.name)
        return self._factory.create(catalog, key.value)
