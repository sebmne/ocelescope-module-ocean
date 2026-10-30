"""The Climatiq adapter of the factor catalog, against a stand-in for its API that
answers as Climatiq documents it."""

import json
import re
from collections.abc import Callable
from pathlib import Path
from typing import Any

import httpx
import pytest

from ocelescope_module_socel.api import dependencies
from ocelescope_module_socel.application.errors import (
    CatalogFactorNotFound,
    CatalogKeyRefused,
    FactorCatalogNotConnected,
    FactorCatalogUnavailable,
    IncompatibleUnit,
    UnknownFactorCatalog,
)
from ocelescope_module_socel.application.ports.factor_catalog import CatalogOffer
from ocelescope_module_socel.application.use_cases.list_factor_catalogs import (
    ListFactorCatalogsCommand,
)
from ocelescope_module_socel.domain.models.factor_catalog import FactorQuery
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.climatiq import (
    ClimatiqConnector,
    ClimatiqFactorCatalog,
)
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.factory import (
    ExternalFactorCatalogFactory,
)

GRID: dict[str, Any] = {
    "id": "f3a6-grid",
    "activity_id": "electricity-supply_grid-source_supplier_mix",
    "name": "Electricity supplied from grid",
    "source": "UBA",
    "source_dataset": "Strommix 2024",
    "year": 2024,
    "region": "DE",
    "region_name": "Germany",
    "unit": "kg/kWh",
    "unit_type": "Energy",
    "factor": None,
    "access_type": "public",
}
STEEL: dict[str, Any] = {
    **GRID,
    "id": "b812-steel",
    "name": "Steel, cold rolled",
    "source": "EPA",
    "source_dataset": None,
    "year": "2023",
    "region": "US",
    "unit": "kg/t",
    "unit_type": "Weight",
    "factor": 2100.0,
}


class Climatiq:
    """Answers search, estimate and data-version requests from fixed factors,
    and keeps what it was asked."""

    def __init__(self, factors: list[dict[str, Any]]) -> None:
        self.factors = factors
        self.requests: list[httpx.Request] = []
        self.refusal: httpx.Response | None = None

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if self.refusal is not None:
            return self.refusal
        path, params = request.url.path, request.url.params
        if path == "/data/v1/data-versions":
            return httpx.Response(200, json={"latest_release": "38", "latest": "38.38"})
        if path == "/data/v1/search":
            found = [
                f
                for f in self.factors
                if params.get("query", "").lower() in f["name"].lower()
                and params.get("id", f["id"]) == f["id"]
                and params.get("unit_type", f["unit_type"]) == f["unit_type"]
            ]
            size = int(params.get("results_per_page", 20))
            page = int(params.get("page", 1))
            return httpx.Response(
                200,
                json={
                    "current_page": page,
                    "last_page": max(1, -(-len(found) // size)),
                    "total_results": len(found),
                    "results": found[(page - 1) * size : page * size],
                    "possible_filters": {},
                },
            )
        if path == "/data/v1/estimate":
            body = json.loads(request.content)
            factor = next(f for f in self.factors if f["id"] == body["emission_factor"]["id"])
            per = {
                ("kWh", "Wh"): 0.001,
                ("kWh", "kWh"): 1.0,
                ("t", "kg"): 0.001,
                ("m3", "m3"): 1.0,
            }
            parameters = body["parameters"]
            unit = next(v for k, v in parameters.items() if k.endswith("_unit"))
            ratio = per.get((factor["unit"].split("/")[1], unit))
            if ratio is None:
                return httpx.Response(
                    400,
                    json={
                        "error": "bad_request",
                        "error_code": "invalid_unit_type_supplied",
                        "message": "The unit type matched no units of the found factors.",
                    },
                )
            value = (factor["factor"] or 0.38) * ratio
            return httpx.Response(200, json={"co2e": value, "co2e_unit": "kg"})
        return httpx.Response(404, json={"error": "not_found", "message": "No such path."})


@pytest.fixture
def climatiq() -> Climatiq:
    return Climatiq([GRID, STEEL])


@pytest.fixture
def catalog(climatiq: Climatiq) -> ClimatiqFactorCatalog:
    client = httpx.Client(
        base_url="https://api.climatiq.io", transport=httpx.MockTransport(climatiq)
    )
    return ClimatiqFactorCatalog(client)


def searches(climatiq: Climatiq) -> list[dict[str, str]]:
    return [dict(r.url.params) for r in climatiq.requests if r.url.path == "/data/v1/search"]


def test_a_search_lists_factors_as_climatiq_does(catalog: ClimatiqFactorCatalog) -> None:
    items, total = catalog.search(FactorQuery(text="electricity"), offset=0, limit=10)

    assert total == 1
    assert [item.model_dump() for item in items] == [
        {
            "ref": "f3a6-grid",
            "name": "Electricity supplied from grid",
            "source": "UBA, Strommix 2024",
            "region": "DE",
            "year": 2024,
            "unit": "kWh",
            "value": None,
        }
    ]


def test_a_listed_value_comes_along_where_climatiq_gives_it(
    catalog: ClimatiqFactorCatalog,
) -> None:
    (steel,), _ = catalog.search(FactorQuery(text="steel"), offset=0, limit=10)

    assert (steel.value, steel.unit, steel.year, steel.source) == (2100.0, "t", 2023, "EPA")


def test_a_search_follows_the_latest_data_release(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq
) -> None:
    catalog.search(FactorQuery(text="steel"), offset=0, limit=10)
    catalog.search(FactorQuery(text="grid"), offset=0, limit=10)

    assert [r.url.path for r in climatiq.requests].count("/data/v1/data-versions") == 1
    assert {params["data_version"] for params in searches(climatiq)} == {"^38"}


def test_a_fixed_data_version_is_kept(climatiq: Climatiq) -> None:
    client = httpx.Client(
        base_url="https://api.climatiq.io", transport=httpx.MockTransport(climatiq)
    )
    ClimatiqFactorCatalog(client, data_version="37").search(
        FactorQuery(text="steel"), offset=0, limit=10
    )

    assert [params["data_version"] for params in searches(climatiq)] == ["37"]


def test_a_search_passes_the_filters_in_climatiqs_terms(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq
) -> None:
    catalog.search(FactorQuery(text="grid", unit="Wh", region="DE", year=2024), offset=0, limit=10)

    (params,) = searches(climatiq)
    assert {k: params[k] for k in ("query", "unit_type", "region", "year")} == {
        "query": "grid",
        "unit_type": "Energy",
        "region": "DE",
        "year": "2024",
    }


def test_a_unit_climatiq_does_not_know_finds_nothing(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq
) -> None:
    assert catalog.search(FactorQuery(text="grid", unit="furlong"), offset=0, limit=10) == (
        (),
        0,
    )
    assert searches(climatiq) == []


@pytest.mark.parametrize(("offset", "limit"), [(0, 1), (1, 1), (1, 2), (2, 3)])
def test_offsets_are_turned_into_climatiqs_pages(offset: int, limit: int) -> None:
    factors = [{**GRID, "id": f"f{i}", "name": f"grid {i}"} for i in range(5)]
    climatiq = Climatiq(factors)
    client = httpx.Client(
        base_url="https://api.climatiq.io", transport=httpx.MockTransport(climatiq)
    )

    items, total = ClimatiqFactorCatalog(client).search(
        FactorQuery(text="grid"), offset=offset, limit=limit
    )

    assert total == 5
    assert [item.ref for item in items] == [f"f{i}" for i in range(offset, min(5, offset + limit))]


def test_a_factor_is_estimated_for_one_unit_of_the_flow(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq
) -> None:
    resolved = catalog.factor("b812-steel", unit="kg")

    assert (resolved.unit, resolved.value) == ("kg", 2.1)
    assert resolved.factor.ref == "b812-steel"
    (estimate,) = [r for r in climatiq.requests if r.url.path == "/data/v1/estimate"]
    assert json.loads(estimate.content) == {
        "emission_factor": {"id": "b812-steel"},
        "parameters": {"weight": 1.0, "weight_unit": "kg"},
    }


def test_a_pint_style_unit_is_given_in_climatiqs_spelling(climatiq: Climatiq) -> None:
    air = {**STEEL, "id": "air", "name": "Compressed air", "unit": "kg/m3", "unit_type": "Volume"}
    climatiq.factors.append(air)
    client = httpx.Client(
        base_url="https://api.climatiq.io", transport=httpx.MockTransport(climatiq)
    )

    resolved = ClimatiqFactorCatalog(client).factor("air", unit="m**3")

    assert (resolved.unit, resolved.value) == ("m**3", 2100.0)
    (estimate,) = [r for r in climatiq.requests if r.url.path == "/data/v1/estimate"]
    assert json.loads(estimate.content)["parameters"] == {"volume": 1.0, "volume_unit": "m3"}


def test_an_unknown_factor_is_not_found(catalog: ClimatiqFactorCatalog) -> None:
    with pytest.raises(CatalogFactorNotFound):
        catalog.factor("nothing", unit="kg")


def test_a_factor_of_another_unit_type_is_refused_without_an_estimate(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq
) -> None:
    with pytest.raises(IncompatibleUnit):
        catalog.factor("b812-steel", unit="kWh")

    assert all(r.url.path != "/data/v1/estimate" for r in climatiq.requests)


def test_a_unit_climatiq_does_not_know_is_refused(catalog: ClimatiqFactorCatalog) -> None:
    with pytest.raises(IncompatibleUnit):
        catalog.factor("b812-steel", unit="furlong")


@pytest.mark.parametrize(
    ("status", "reason"),
    [
        (401, "Climatiq refused the API key: Invalid API key."),
        (429, "Climatiq's quota or rate limit is reached: Invalid API key."),
        (503, "Climatiq cannot answer right now: Invalid API key."),
    ],
)
def test_a_refusal_makes_the_catalog_unavailable(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq, status: int, reason: str
) -> None:
    climatiq.refusal = httpx.Response(
        status, json={"error": "x", "error_code": None, "message": "Invalid API key."}
    )

    with pytest.raises(FactorCatalogUnavailable, match=re.escape(reason)):
        catalog.search(FactorQuery(text="grid"), offset=0, limit=10)


def test_an_unreachable_climatiq_makes_the_catalog_unavailable() -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route", request=request)

    client = httpx.Client(base_url="https://api.climatiq.io", transport=httpx.MockTransport(fail))

    with pytest.raises(FactorCatalogUnavailable, match="cannot be reached"):
        ClimatiqFactorCatalog(client).search(FactorQuery(text="grid"), offset=0, limit=10)


def test_an_accepted_key_passes_the_check(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq
) -> None:
    catalog.check()

    assert searches(climatiq) == [{"data_version": "^38", "results_per_page": "1"}]


@pytest.mark.parametrize("status", [401, 403])
def test_a_refused_key_fails_the_check(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq, status: int
) -> None:
    climatiq.refusal = httpx.Response(status, json={"message": "Invalid API key."})

    with pytest.raises(CatalogKeyRefused, match="Climatiq does not accept this key."):
        catalog.check()


def test_an_unreachable_climatiq_fails_the_check_as_unavailable(
    catalog: ClimatiqFactorCatalog, climatiq: Climatiq
) -> None:
    climatiq.refusal = httpx.Response(503, json={"message": "Down."})

    with pytest.raises(FactorCatalogUnavailable) as raised:
        catalog.check()
    assert not isinstance(raised.value, CatalogKeyRefused)


def test_the_connector_keeps_the_catalog_of_the_key_last_used() -> None:
    connector = ClimatiqConnector()

    first = connector.connect("one")

    assert connector.connect("one") is first
    assert connector.connect("two") is not first


def test_the_factory_offers_climatiq() -> None:
    factory = ExternalFactorCatalogFactory()

    assert factory.offered() == (CatalogOffer("climatiq", "Climatiq"),)
    assert factory.offer("climatiq").name == "Climatiq"
    assert isinstance(factory.create("climatiq", "secret"), ClimatiqFactorCatalog)


@pytest.mark.parametrize("make", [lambda f: f.offer("nowhere"), lambda f: f.create("nowhere", "k")])
def test_the_factory_knows_no_other_catalog(
    make: Callable[[ExternalFactorCatalogFactory], object],
) -> None:
    with pytest.raises(UnknownFactorCatalog):
        make(ExternalFactorCatalogFactory())


def test_climatiq_is_on_offer(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CLIMATIQ_API_KEY", raising=False)

    infos = dependencies.get_list_factor_catalogs(
        dependencies.get_factor_catalog_factory(), dependencies.get_catalog_credentials()
    ).execute(ListFactorCatalogsCommand())

    assert [info.model_dump() for info in infos] == [
        {"id": "climatiq", "name": "Climatiq", "available": False, "key": None}
    ]


def open_climatiq() -> object:
    return dependencies.get_open_factor_catalog(
        dependencies.get_factor_catalog_factory(), dependencies.get_catalog_credentials()
    ).open("climatiq")


def test_a_key_in_the_environment_opens_climatiq(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CLIMATIQ_API_KEY", "secret")

    assert isinstance(open_climatiq(), ClimatiqFactorCatalog)


def test_without_a_key_climatiq_stays_closed(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.setenv("CLIMATIQ_API_KEY", "  ")

    with pytest.raises(FactorCatalogNotConnected):
        open_climatiq()


def test_a_saved_key_is_kept_in_the_data_folder(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    monkeypatch.delenv("CLIMATIQ_API_KEY", raising=False)

    dependencies.get_catalog_credentials().save("climatiq", "secret")

    assert (tmp_path / "socel" / "factor_catalogs.json").exists()
