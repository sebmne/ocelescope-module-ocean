"""Public resource locations include the Ocelescope module mount."""

from fastapi import FastAPI
from fastapi.testclient import TestClient
from ocelescope_backend.app.dependencies import get_session
from ocelescope_backend.app.internal.session import Session
from ocelescope_backend.app.modules.loader import build_module

from ocelescope_module_socel.module import Socel


def test_created_resource_location_resolves_under_the_module_mount(
    session: Session, plain_log: str
) -> None:
    module = build_module(Socel).create_app()
    module.dependency_overrides[get_session] = lambda: session
    host = FastAPI()
    host.mount("/modules/socel/v1", module)
    with TestClient(host) as client:
        result = client.post(
            f"/modules/socel/v1/logs/{plain_log}/derivations", json={"name": "prepared"}
        )
        assert result.status_code == 201
        assert result.headers["location"] == (
            f"http://testserver/modules/socel/v1/logs/{result.json()['ocelId']}/summary"
        )
        assert client.get(result.headers["location"]).status_code == 200
