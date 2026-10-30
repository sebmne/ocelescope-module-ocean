from dataclasses import dataclass

from ocelescope_module_socel.application.ports.catalog_credentials import (
    CatalogCredentials,
    CatalogKey,
)
from ocelescope_module_socel.application.ports.factor_catalog import (
    CatalogOffer,
    FactorCatalogFactory,
)
from ocelescope_module_socel.domain.models.factor_catalog import FactorCatalogInfo


@dataclass(frozen=True, kw_only=True)
class ListFactorCatalogsCommand:
    pass


class ListFactorCatalogs:
    """The factor catalogs on offer, and whether each has a key to be consulted with."""

    def __init__(self, *, factory: FactorCatalogFactory, credentials: CatalogCredentials) -> None:
        self._factory = factory
        self._credentials = credentials

    def execute(self, command: ListFactorCatalogsCommand) -> tuple[FactorCatalogInfo, ...]:
        return tuple(
            catalog_info(offer, self._credentials.key(offer.id))
            for offer in self._factory.offered()
        )


def catalog_info(offer: CatalogOffer, key: CatalogKey | None) -> FactorCatalogInfo:
    return FactorCatalogInfo(
        id=offer.id,
        name=offer.name,
        available=key is not None,
        key=key.source if key is not None else None,
    )
