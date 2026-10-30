from dataclasses import dataclass, field

from ocelescope_module_socel.application.errors import CatalogKeyFromEnvironment
from ocelescope_module_socel.application.ports.catalog_credentials import CatalogCredentials
from ocelescope_module_socel.application.ports.factor_catalog import FactorCatalogFactory
from ocelescope_module_socel.application.use_cases.list_factor_catalogs import catalog_info
from ocelescope_module_socel.domain.models.factor_catalog import FactorCatalogInfo


@dataclass(frozen=True, kw_only=True)
class ConnectFactorCatalogCommand:
    catalog: str
    key: str = field(repr=False)


class ConnectFactorCatalog:
    """Keeps the user's key for a factor catalog, once the catalog accepts it. A
    key set in the environment is not replaced."""

    def __init__(self, *, factory: FactorCatalogFactory, credentials: CatalogCredentials) -> None:
        self._factory = factory
        self._credentials = credentials

    def execute(self, command: ConnectFactorCatalogCommand) -> FactorCatalogInfo:
        key = command.key.strip()
        if not key:
            raise ValueError("A key is needed.")
        offer = self._factory.offer(command.catalog)
        current = self._credentials.key(offer.id)
        if current is not None and current.source == "environment":
            raise CatalogKeyFromEnvironment()
        # Raises CatalogKeyRefused, or FactorCatalogUnavailable, before anything is kept.
        self._factory.create(offer.id, key).check()
        self._credentials.save(offer.id, key)
        return catalog_info(offer, self._credentials.key(offer.id))
