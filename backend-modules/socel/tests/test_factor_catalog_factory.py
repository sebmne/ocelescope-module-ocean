"""The factory that offers and creates the external factor catalogs of its providers."""

from collections.abc import Callable
from typing import ClassVar

import pytest

from ocelescope_module_socel.application.errors import UnknownFactorCatalog
from ocelescope_module_socel.application.ports.factor_catalog import CatalogOffer, FactorSlice
from ocelescope_module_socel.domain.models.factor_catalog import FactorQuery, ResolvedFactor
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.factory import (
    ExternalFactorCatalogFactory,
)


class Opened:
    """Stands in for a catalog: records the key it was opened with."""

    def __init__(self, key: str) -> None:
        self.key = key

    def check(self) -> None: ...

    def search(self, query: FactorQuery, *, offset: int, limit: int) -> FactorSlice:
        raise NotImplementedError

    def factor(self, ref: str, *, unit: str) -> ResolvedFactor:
        raise NotImplementedError


class First:
    offer: ClassVar[CatalogOffer] = CatalogOffer("first", "First", "https://first.example")

    def connect(self, key: str) -> Opened:
        return Opened(key)


class Second:
    offer: ClassVar[CatalogOffer] = CatalogOffer("second", "Second", "https://second.example")

    def connect(self, key: str) -> Opened:
        return Opened(key)


def test_the_providers_are_offered_in_their_order() -> None:
    factory = ExternalFactorCatalogFactory([Second(), First()])

    assert factory.offered() == (Second.offer, First.offer)
    assert factory.offer("first") is First.offer


def test_a_catalog_is_opened_by_its_provider() -> None:
    opened = ExternalFactorCatalogFactory([First(), Second()]).create("second", "key")

    assert isinstance(opened, Opened)
    assert opened.key == "key"


@pytest.mark.parametrize(
    "ask",
    [lambda factory: factory.offer("nowhere"), lambda factory: factory.create("nowhere", "k")],
)
def test_an_id_no_provider_offers_is_unknown(
    ask: Callable[[ExternalFactorCatalogFactory], object],
) -> None:
    with pytest.raises(UnknownFactorCatalog):
        ask(ExternalFactorCatalogFactory([First()]))


def test_two_providers_cannot_share_an_id() -> None:
    with pytest.raises(ValueError, match="'first'"):
        ExternalFactorCatalogFactory([First(), First()])
