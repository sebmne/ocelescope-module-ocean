from dataclasses import dataclass

from ocelescope_module_socel.application.errors import CatalogKeyFromEnvironment
from ocelescope_module_socel.application.ports.catalog_credentials import CatalogCredentials
from ocelescope_module_socel.application.ports.factor_catalog import FactorCatalogFactory


@dataclass(frozen=True, kw_only=True)
class DisconnectFactorCatalogCommand:
    catalog: str


class DisconnectFactorCatalog:
    """Forgets the key kept for a factor catalog; one set in the environment stays."""

    def __init__(self, *, factory: FactorCatalogFactory, credentials: CatalogCredentials) -> None:
        self._factory = factory
        self._credentials = credentials

    def execute(self, command: DisconnectFactorCatalogCommand) -> None:
        offer = self._factory.offer(command.catalog)
        current = self._credentials.key(offer.id)
        if current is not None and current.source == "environment":
            raise CatalogKeyFromEnvironment()
        self._credentials.remove(offer.id)
