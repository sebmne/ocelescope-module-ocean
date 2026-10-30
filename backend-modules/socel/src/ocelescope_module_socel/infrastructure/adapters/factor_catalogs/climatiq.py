"""Climatiq's emission factors (https://www.climatiq.io), through its data API."""

from threading import Lock
from typing import Any, ClassVar

import httpx

from ocelescope_module_socel.application.errors import (
    CatalogFactorNotFound,
    CatalogKeyRefused,
    FactorCatalogUnavailable,
    IncompatibleUnit,
)
from ocelescope_module_socel.application.ports.factor_catalog import CatalogOffer, FactorSlice
from ocelescope_module_socel.domain.models.factor_catalog import (
    CatalogFactor,
    FactorQuery,
    ResolvedFactor,
)
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.climatiq_units import (
    climatiq_unit,
)

BASE_URL = "https://api.climatiq.io"
_TIMEOUT = httpx.Timeout(15.0, connect=5.0)
# An estimate's co2e, in kg per unit it may be given in.
_KG = {"g": 0.001, "kg": 1.0, "t": 1000.0, "lb": 0.45359237}
_NOT_FOUND = {"no_emission_factors_found", "no_matching_resource_found"}


class ClimatiqFactorCatalog:
    """Searches Climatiq's factors, and resolves one by estimating the emissions
    of one unit of a flow with it: Climatiq converts the units itself.

    `data_version` is Climatiq's: a fixed release ("38"), or the latest within
    one ("^38"). Without it, the latest release is asked for once and followed.
    """

    # What the module offers Climatiq as: its id, the name users see, and its
    # website. Written here only; the connector, the factory and the messages
    # below read it.
    offer: ClassVar[CatalogOffer] = CatalogOffer(
        id="climatiq", name="Climatiq", website="https://www.climatiq.io"
    )

    def __init__(self, client: httpx.Client, *, data_version: str | None = None) -> None:
        self._client = client
        self._data_version = data_version
        self._lock = Lock()

    @classmethod
    def connect(cls, api_key: str, *, data_version: str | None = None) -> "ClimatiqFactorCatalog":
        client = httpx.Client(
            base_url=BASE_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            timeout=_TIMEOUT,
        )
        return cls(client, data_version=data_version)

    def check(self) -> None:
        try:
            self._get("/data/v1/search", {"data_version": self._version(), "results_per_page": 1})
        except _KeyRefused as error:
            raise CatalogKeyRefused(self.offer.name) from error

    def search(self, query: FactorQuery, *, offset: int, limit: int) -> FactorSlice:
        params: dict[str, Any] = {
            "data_version": self._version(),
            "query": query.text,
            "results_per_page": limit,
        }
        if query.region is not None:
            params["region"] = query.region
        if query.year is not None:
            params["year"] = query.year
        if query.unit is not None:
            unit = climatiq_unit(query.unit)
            if unit is None:
                # No factor can be expressed per a unit Climatiq does not know.
                return (), 0
            params["unit_type"] = unit.unit_type

        # Climatiq pages by number: the slice lies in at most two of its pages.
        first = offset // limit
        skip = offset - first * limit
        results: list[dict[str, Any]] = []
        total = 0
        for page in range(first + 1, first + (3 if skip else 2)):
            body = self._get("/data/v1/search", {**params, "page": page})
            total = int(body["total_results"])
            results.extend(body["results"])
            if page >= int(body["last_page"]):
                break
        return tuple(_listed(result) for result in results[skip : skip + limit]), total

    def factor(self, ref: str, *, unit: str) -> ResolvedFactor:
        target = climatiq_unit(unit)
        if target is None:
            raise IncompatibleUnit(ref, unit)
        listing = self._get("/data/v1/search", {"data_version": self._version(), "id": ref})
        if not listing["results"]:
            raise CatalogFactorNotFound(ref)
        listed = listing["results"][0]
        if str(listed.get("unit_type", "")).lower() != target.unit_type.lower():
            raise IncompatibleUnit(ref, unit)

        response = self._send(
            "POST",
            "/data/v1/estimate",
            json={"emission_factor": {"id": ref}, "parameters": target.parameters(1.0)},
        )
        if response.status_code in (400, 404):
            code = _error(response).get("error_code")
            if code == "invalid_unit_type_supplied":
                raise IncompatibleUnit(ref, unit)
            if code in _NOT_FOUND or response.status_code == 404:
                raise CatalogFactorNotFound(ref)
        estimate = _body(response)
        per_kg = _KG.get(str(estimate.get("co2e_unit", "kg")))
        if per_kg is None:
            raise FactorCatalogUnavailable(
                f"{self.offer.name} answered in an unknown unit, {estimate.get('co2e_unit')!r}."
            )
        return ResolvedFactor(
            unit=unit,
            value=float(estimate["co2e"]) * per_kg,
            factor=_listed(listed),
        )

    def _version(self) -> str:
        with self._lock:
            if self._data_version is None:
                release = self._get("/data/v1/data-versions", {})["latest_release"]
                self._data_version = f"^{release}"
            return self._data_version

    def _get(self, path: str, params: dict[str, Any]) -> dict[str, Any]:
        return _body(self._send("GET", path, params=params))

    def _send(self, method: str, path: str, **kwargs: Any) -> httpx.Response:
        try:
            return self._client.request(method, path, **kwargs)
        except httpx.HTTPError as error:
            raise FactorCatalogUnavailable(
                f"{self.offer.name} cannot be reached: {error}"
            ) from error


def _body(response: httpx.Response) -> dict[str, Any]:
    """The answer's JSON; a refusal as FactorCatalogUnavailable, with Climatiq's reason."""
    if response.is_success:
        return response.json()
    message = _error(response).get("message") or response.reason_phrase
    name = ClimatiqFactorCatalog.offer.name
    if response.status_code in (401, 403):
        raise _KeyRefused(f"{name} refused the API key: {message}")
    if response.status_code == 429:
        reason = f"{name}'s quota or rate limit is reached"
    elif response.status_code >= 500:
        reason = f"{name} cannot answer right now"
    else:
        reason = f"{name} refused the request"
    raise FactorCatalogUnavailable(f"{reason}: {message}")


class _KeyRefused(FactorCatalogUnavailable):
    """Climatiq does not accept the key."""


def _error(response: httpx.Response) -> dict[str, Any]:
    """Climatiq's error body: error, error_code and message."""
    try:
        body = response.json()
    except ValueError:
        return {}
    return body if isinstance(body, dict) else {}


def _listed(result: dict[str, Any]) -> CatalogFactor:
    source = str(result.get("source") or "")
    dataset = result.get("source_dataset")
    year = result.get("year")
    factor = result.get("factor")
    return CatalogFactor(
        ref=str(result["id"]),
        name=str(result["name"]),
        source=f"{source}, {dataset}" if dataset else source,
        region=result.get("region") or None,
        year=int(year) if year is not None and str(year).isdigit() else None,
        unit=_per(str(result.get("unit") or result.get("unit_type") or "")),
        value=float(factor) if factor is not None else None,
    )


def _per(unit: str) -> str:
    """The unit a factor is per: "kWh" of "kg/kWh"."""
    return unit.split("/", 1)[1] if "/" in unit else unit


class ClimatiqConnector:
    """Opens Climatiq with a key, and keeps it open for the key last used: its
    connections and the data version it looked up serve the next requests."""

    offer: ClassVar[CatalogOffer] = ClimatiqFactorCatalog.offer

    def __init__(self, *, data_version: str | None = None) -> None:
        self._data_version = data_version
        self._open: tuple[str, ClimatiqFactorCatalog] | None = None
        self._lock = Lock()

    def connect(self, key: str) -> ClimatiqFactorCatalog:
        with self._lock:
            if self._open is not None and self._open[0] == key:
                return self._open[1]
            # The catalog of another key is let go, not closed: a request may
            # still be using it.
            catalog = ClimatiqFactorCatalog.connect(key, data_version=self._data_version)
            self._open = (key, catalog)
            return catalog
