from dataclasses import dataclass
from typing import Protocol

from ocelescope_module_socel.domain.models.factor_catalog import (
    CatalogFactor,
    FactorQuery,
    ResolvedFactor,
)

# Items and the total matching the query.
type FactorSlice = tuple[tuple[CatalogFactor, ...], int]


class FactorCatalog(Protocol):
    """An external database of emission factors in kg CO2e, consulted while a
    flow's factors are chosen (e.g. Climatiq or openLCA), opened with a key.

    Raises (every method):
        FactorCatalogUnavailable: If the catalog has no key, or cannot be
            reached or refuses the module's requests right now.
    """

    def check(self) -> None:
        """Whether the catalog can be consulted with its key, by asking it once.

        Raises:
            CatalogKeyRefused: If the catalog does not accept the key.
        """
        ...

    def search(self, query: FactorQuery, *, offset: int, limit: int) -> FactorSlice:
        """A slice of the factors matching the query, best match first, with
        their total."""
        ...

    def factor(self, ref: str, *, unit: str) -> ResolvedFactor:
        """The listed factor in kg CO2e per one `unit`.

        Raises:
            CatalogFactorNotFound: If the catalog has no factor `ref`.
            IncompatibleUnit: If the factor cannot be expressed per `unit`.
        """
        ...


@dataclass(frozen=True)
class CatalogOffer:
    """A factor catalog on offer: its id and its name as the user knows it."""

    id: str
    name: str


class FactorCatalogFactory(Protocol):
    """Creates the factor catalogs on offer, by id."""

    def offered(self) -> tuple[CatalogOffer, ...]:
        """Every catalog on offer, in the order they are shown."""
        ...

    def offer(self, catalog: str) -> CatalogOffer:
        """The catalog on offer under `catalog`.

        Raises:
            UnknownFactorCatalog: If no catalog is offered under that id.
        """
        ...

    def create(self, catalog: str, key: str) -> FactorCatalog:
        """The catalog, consulted with `key`; nothing is asked of it yet, so a
        key it refuses shows on the first call (see `FactorCatalog.check`).

        Raises:
            UnknownFactorCatalog: If no catalog is offered under that id.
        """
        ...
