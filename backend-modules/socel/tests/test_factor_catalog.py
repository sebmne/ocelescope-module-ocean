"""Consulting external catalogs of emission factors, through their ports."""

from collections.abc import Callable, Iterator

import pytest
from api import Api
from fastapi.testclient import TestClient
from httpx import Response
from ocelescope_backend.app.modules.loader import build_module

from ocelescope_module_socel.api.dependencies import (
    get_catalog_credentials,
    get_factor_catalog_factory,
)
from ocelescope_module_socel.application.errors import (
    CatalogFactorNotFound,
    CatalogKeyRefused,
    IncompatibleUnit,
    UnknownFactorCatalog,
)
from ocelescope_module_socel.application.ports.catalog_credentials import CatalogKey
from ocelescope_module_socel.application.ports.factor_catalog import CatalogOffer, FactorSlice
from ocelescope_module_socel.domain.models.factor_catalog import (
    CatalogFactor,
    FactorQuery,
    ResolvedFactor,
)
from ocelescope_module_socel.module import Socel

GRID = CatalogFactor(
    ref="electricity/grid-de",
    name="Electricity, grid mix",
    source="UBA",
    region="DE",
    year=2024,
    unit="kWh",
    value=0.38,
)
STEEL = CatalogFactor(
    ref="steel-cold-rolled",
    name="Steel, cold rolled",
    source="EPA",
    region=None,
    year=2023,
    unit="t",
    value=2100.0,
)
# Per what the fake knows each factor, and how many of those make one unit.
CONVERSIONS = {("kWh", "kWh"): 1.0, ("kWh", "Wh"): 0.001, ("t", "kg"): 0.001}
GOOD_KEY = "good-key"


class FakeCatalog:
    """A catalog of two factors that accepts one key and records what it was asked."""

    def __init__(self) -> None:
        self.key: str | None = None
        self.queries: list[tuple[FactorQuery, int, int]] = []

    def check(self) -> None:
        if self.key != GOOD_KEY:
            raise CatalogKeyRefused("Fake")

    def search(self, query: FactorQuery, *, offset: int, limit: int) -> FactorSlice:
        self.queries.append((query, offset, limit))
        found = [f for f in (GRID, STEEL) if query.text.lower() in f.name.lower()]
        return tuple(found[offset : offset + limit]), len(found)

    def factor(self, ref: str, *, unit: str) -> ResolvedFactor:
        listed = next((f for f in (GRID, STEEL) if f.ref == ref), None)
        if listed is None:
            raise CatalogFactorNotFound(ref)
        per = CONVERSIONS.get((listed.unit, unit))
        if per is None:
            raise IncompatibleUnit(ref, unit)
        assert listed.value is not None  # the fake lists every value
        return ResolvedFactor(unit=unit, value=listed.value * per, factor=listed)


class FakeFactory:
    """Offers "fake", the catalog the tests watch, and "other", one more."""

    def __init__(self, catalog: FakeCatalog) -> None:
        self.catalogs = {"fake": catalog, "other": FakeCatalog()}
        self.offers = (
            CatalogOffer("fake", "Fake", "https://fake.example"),
            CatalogOffer("other", "Other", "https://other.example"),
        )

    def offered(self) -> tuple[CatalogOffer, ...]:
        return self.offers

    def offer(self, catalog: str) -> CatalogOffer:
        found = next((offer for offer in self.offers if offer.id == catalog), None)
        if found is None:
            raise UnknownFactorCatalog(catalog)
        return found

    def create(self, catalog: str, key: str) -> FakeCatalog:
        self.offer(catalog)
        self.catalogs[catalog].key = key
        return self.catalogs[catalog]


class MemoryCredentials:
    """Keys by catalog: set in the environment, or saved."""

    def __init__(self) -> None:
        self.environment: dict[str, str] = {}
        self.saved: dict[str, str] = {"fake": GOOD_KEY}

    def key(self, catalog: str) -> CatalogKey | None:
        if catalog in self.environment:
            return CatalogKey(self.environment[catalog], "environment")
        saved = self.saved.get(catalog)
        return CatalogKey(saved, "saved") if saved is not None else None

    def save(self, catalog: str, key: str) -> None:
        self.saved[catalog] = key

    def remove(self, catalog: str) -> None:
        self.saved.pop(catalog, None)


@pytest.fixture
def catalog() -> FakeCatalog:
    return FakeCatalog()


@pytest.fixture
def credentials() -> MemoryCredentials:
    """A saved key "fake" accepts, none for "other"; tests change them as they need."""
    return MemoryCredentials()


@pytest.fixture
def catalog_api(catalog: FakeCatalog, credentials: MemoryCredentials) -> Iterator[Api]:
    factory = FakeFactory(catalog)
    app = build_module(Socel).create_app()
    app.dependency_overrides[get_catalog_credentials] = lambda: credentials
    app.dependency_overrides[get_factor_catalog_factory] = lambda: factory
    with TestClient(app) as client:
        yield Api(client)


def test_every_catalog_is_listed_with_its_key(catalog_api: Api) -> None:
    assert catalog_api.list_factor_catalogs().json() == [
        {
            "id": "fake",
            "name": "Fake",
            "website": "https://fake.example",
            "available": True,
            "key": "saved",
        },
        {
            "id": "other",
            "name": "Other",
            "website": "https://other.example",
            "available": False,
            "key": None,
        },
    ]


def test_a_key_in_the_environment_is_told_apart(
    catalog_api: Api, credentials: MemoryCredentials
) -> None:
    credentials.environment["other"] = GOOD_KEY

    other = catalog_api.list_factor_catalogs().json()[1]

    assert (other["available"], other["key"]) == (True, "environment")


def test_a_catalog_without_a_key_cannot_be_searched(catalog_api: Api) -> None:
    response = catalog_api.search_factor_catalog("other", "electricity")

    assert response.status_code == 503
    assert response.json() == {"detail": "Other is not connected; connect it with a key first."}


def test_a_catalog_without_a_key_resolves_nothing(catalog_api: Api) -> None:
    assert catalog_api.resolve_catalog_factor("other", "steel", "kg").status_code == 503


@pytest.mark.parametrize(
    "call",
    [
        lambda api: api.search_factor_catalog("nowhere", "steel"),
        lambda api: api.resolve_catalog_factor("nowhere", "steel", "kg"),
        lambda api: api.connect_factor_catalog("nowhere", GOOD_KEY),
        lambda api: api.disconnect_factor_catalog("nowhere"),
    ],
)
def test_an_unknown_catalog_is_not_found(catalog_api: Api, call: Callable[[Api], Response]) -> None:
    response = call(catalog_api)

    assert response.status_code == 404
    assert response.json() == {"detail": "There is no factor catalog 'nowhere'."}


def test_an_accepted_key_is_saved(catalog_api: Api, credentials: MemoryCredentials) -> None:
    credentials.saved.clear()

    response = catalog_api.connect_factor_catalog("fake", f"  {GOOD_KEY} ")

    assert response.status_code == 200
    assert response.json() == {
        "id": "fake",
        "name": "Fake",
        "website": "https://fake.example",
        "available": True,
        "key": "saved",
    }
    assert credentials.saved == {"fake": GOOD_KEY}


def test_a_refused_key_is_not_saved(catalog_api: Api, credentials: MemoryCredentials) -> None:
    credentials.saved.clear()

    response = catalog_api.connect_factor_catalog("fake", "wrong")

    assert response.status_code == 422
    assert response.json() == {"detail": "Fake does not accept this key."}
    assert credentials.saved == {}


def test_a_refused_key_keeps_the_saved_one(
    catalog_api: Api, credentials: MemoryCredentials
) -> None:
    catalog_api.connect_factor_catalog("fake", "wrong")

    assert credentials.saved == {"fake": GOOD_KEY}


def test_a_key_is_needed_to_connect(catalog_api: Api, credentials: MemoryCredentials) -> None:
    assert catalog_api.connect_factor_catalog("fake", "   ").status_code == 422
    assert credentials.saved == {"fake": GOOD_KEY}


def test_a_key_in_the_environment_is_not_replaced(
    catalog_api: Api, credentials: MemoryCredentials
) -> None:
    credentials.environment["fake"] = GOOD_KEY

    response = catalog_api.connect_factor_catalog("fake", GOOD_KEY)

    assert response.status_code == 409
    assert "environment" in response.json()["detail"]


def test_disconnecting_forgets_the_saved_key(
    catalog_api: Api, credentials: MemoryCredentials
) -> None:
    assert catalog_api.disconnect_factor_catalog("fake").status_code == 204
    assert credentials.saved == {}
    assert catalog_api.list_factor_catalogs().json()[0]["available"] is False


def test_a_key_in_the_environment_cannot_be_disconnected(
    catalog_api: Api, credentials: MemoryCredentials
) -> None:
    credentials.environment["fake"] = GOOD_KEY

    assert catalog_api.disconnect_factor_catalog("fake").status_code == 409


def test_a_search_lists_factors_as_the_catalog_does(catalog_api: Api) -> None:
    page = catalog_api.search_factor_catalog("fake", "electricity").json()

    assert page == {
        "items": [
            {
                "ref": "electricity/grid-de",
                "name": "Electricity, grid mix",
                "source": "UBA",
                "region": "DE",
                "year": 2024,
                "unit": "kWh",
                "value": 0.38,
            }
        ],
        "total": 1,
        "offset": 0,
        "limit": 50,
    }


def test_a_search_opens_the_catalog_with_its_key(catalog_api: Api, catalog: FakeCatalog) -> None:
    catalog_api.search_factor_catalog("fake", "steel")

    assert catalog.key == GOOD_KEY


def test_a_search_passes_its_filters_on_cleaned(catalog_api: Api, catalog: FakeCatalog) -> None:
    catalog_api.search_factor_catalog(
        "fake", "  steel ", unit="kg", region=" ", year=2023, offset=10, limit=5
    )

    assert catalog.queries == [
        (FactorQuery(text="steel", unit="kg", region=None, year=2023), 10, 5)
    ]


@pytest.mark.parametrize("text", ["", "   "])
def test_a_search_needs_text(catalog_api: Api, catalog: FakeCatalog, text: str) -> None:
    assert catalog_api.search_factor_catalog("fake", text).status_code == 422
    assert catalog.queries == []


def test_a_factor_is_resolved_per_unit_of_the_flow(catalog_api: Api) -> None:
    resolved = catalog_api.resolve_catalog_factor("fake", "steel-cold-rolled", "kg").json()

    assert (resolved["unit"], resolved["value"]) == ("kg", 2.1)
    assert resolved["factor"]["ref"] == "steel-cold-rolled"


def test_a_reference_may_hold_slashes(catalog_api: Api) -> None:
    resolved = catalog_api.resolve_catalog_factor("fake", "electricity/grid-de", "Wh").json()

    assert resolved["value"] == pytest.approx(0.00038)


def test_an_unknown_factor_is_not_found(catalog_api: Api) -> None:
    response = catalog_api.resolve_catalog_factor("fake", "nothing", "kg")

    assert response.status_code == 404
    assert response.json() == {"detail": "The factor catalog has no factor 'nothing'."}


def test_a_factor_in_an_incompatible_unit_is_refused(catalog_api: Api) -> None:
    response = catalog_api.resolve_catalog_factor("fake", "steel-cold-rolled", "kWh")

    assert response.status_code == 422
    assert response.json() == {
        "detail": "The factor 'steel-cold-rolled' cannot be expressed per 'kWh'."
    }


def test_a_factor_needs_a_unit(catalog_api: Api) -> None:
    assert catalog_api.resolve_catalog_factor("fake", "steel-cold-rolled", " ").status_code == 422
