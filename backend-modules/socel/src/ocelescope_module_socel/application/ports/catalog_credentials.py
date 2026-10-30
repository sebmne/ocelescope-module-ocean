from dataclasses import dataclass, field
from typing import Protocol

from ocelescope_module_socel.domain.models.factor_catalog import KeySource


@dataclass(frozen=True)
class CatalogKey:
    """A factor catalog's API key, and where it comes from."""

    value: str = field(repr=False)
    source: KeySource


class CatalogCredentials(Protocol):
    """Where the factor catalogs' API keys are kept, one per catalog id. A key
    set in the environment comes before one saved from the app, and is not
    changed by it."""

    def key(self, catalog: str) -> CatalogKey | None:
        """The catalog's key in use, None when it has none."""
        ...

    def save(self, catalog: str, key: str) -> None:
        """Keep `key` for the catalog across restarts, in place of a saved one."""
        ...

    def remove(self, catalog: str) -> None:
        """Forget the key saved for the catalog, if there is one."""
        ...
