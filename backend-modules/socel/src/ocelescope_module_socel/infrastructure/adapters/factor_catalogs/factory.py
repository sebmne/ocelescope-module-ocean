from collections.abc import Iterable
from typing import ClassVar, Protocol

from ocelescope_module_socel.application.errors import UnknownFactorCatalog
from ocelescope_module_socel.application.ports.factor_catalog import CatalogOffer, FactorCatalog


class CatalogProvider(Protocol):
    """One external catalog: what it is offered as, and how it is opened with a
    key. Each catalog's module provides one (e.g. `ClimatiqConnector`)."""

    offer: ClassVar[CatalogOffer]

    def connect(self, key: str) -> FactorCatalog: ...


class ExternalFactorCatalogFactory:
    """Creates the external factor catalogs of the providers it is given, offered
    in that order; it knows no catalog itself."""

    def __init__(self, providers: Iterable[CatalogProvider]) -> None:
        self._providers: dict[str, CatalogProvider] = {}
        for provider in providers:
            if provider.offer.id in self._providers:
                raise ValueError(f"Two factor catalogs are offered as {provider.offer.id!r}.")
            self._providers[provider.offer.id] = provider

    def offered(self) -> tuple[CatalogOffer, ...]:
        return tuple(provider.offer for provider in self._providers.values())

    def offer(self, catalog: str) -> CatalogOffer:
        return self._provider(catalog).offer

    def create(self, catalog: str, key: str) -> FactorCatalog:
        return self._provider(catalog).connect(key)

    def _provider(self, catalog: str) -> CatalogProvider:
        provider = self._providers.get(catalog)
        if provider is None:
            raise UnknownFactorCatalog(catalog)
        return provider
