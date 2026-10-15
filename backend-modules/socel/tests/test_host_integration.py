"""sOCEL recognition and round trips through the installed Ocelescope host.

These tests deliberately use the host's metadata/download routes and file import,
not a module-specific serializer or a mocked extension registry.
"""

from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from urllib.parse import unquote

import pytest
from api import Api
from conftest import build
from example_log import FLOWS
from fastapi import FastAPI
from fastapi.testclient import TestClient
from ocelescope import OCEL
from ocelescope_backend.app.dependencies import get_session
from ocelescope_backend.app.internal.session import Session
from ocelescope_backend.app.modules.loader import build_module, get_module_path
from ocelescope_module_ocel.module import Ocel

from ocelescope_module_socel.module import Socel

HOST_OCEL = "/modules/ocel/v1"
HOST_SOCEL = "/modules/socel/v1"


@pytest.fixture
def host(session: Session) -> Iterator[TestClient]:
    app = FastAPI()
    for module_class in (Ocel, Socel):
        module = build_module(module_class).create_app()
        module.dependency_overrides[get_session] = lambda: session
        app.mount(get_module_path(module_class), module)
    with TestClient(app) as client:
        yield client


def extension_names(host: TestClient, ocel_id: str) -> set[str]:
    response = host.get(f"{HOST_OCEL}/{ocel_id}")
    assert response.status_code == 200, response.text
    return {extension["name"] for extension in response.json()["extensions"]}


def snapshot(ocel: OCEL) -> dict[str, list[tuple]]:
    """The retained extension data, independently of its library representations."""
    queries = {
        "flows": "SELECT flow_id, unit, category, external_ref FROM socel_flow ORDER BY 1",
        "intervals": (
            "SELECT record_id, flow_id, object_id, quantity, start_time, end_time "
            "FROM socel_interval_records ORDER BY record_id"
        ),
        "event_records": (
            "SELECT record_id, flow_id, object_id, quantity, event_id "
            "FROM socel_event_records ORDER BY record_id"
        ),
        "containment": (
            "SELECT flow_id, object_id, parent_object_id "
            "FROM socel_containedin ORDER BY flow_id, object_id"
        ),
        "event_classes": 'SELECT "ocel:eid", socel_class FROM events ORDER BY 1',
        "object_classes": (
            'SELECT "ocel:oid", "ocel:timestamp", socel_class FROM object_changes '
            "WHERE \"ocel:field\" = 'socel_class' ORDER BY 1, 2"
        ),
    }
    columns = {row[0] for row in ocel.sql("DESCRIBE events").fetchall()}
    if "socel_end_time" in columns:
        queries["event_ends"] = 'SELECT "ocel:eid", socel_end_time FROM events ORDER BY 1'
    return {key: ocel.sql(query).fetchall() for key, query in queries.items()}


def test_host_discovers_socel_and_reports_its_metadata(
    host: TestClient, plain_log: str, socel: str
) -> None:
    assert "socel" not in extension_names(host, plain_log)
    response = host.get(f"{HOST_OCEL}/{socel}")
    assert response.status_code == 200
    assert {"name": "socel", "label": "sOCEL"} in response.json()["extensions"]

    listed = host.get(f"{HOST_OCEL}/ocels")
    assert listed.status_code == 200
    logs = {log["id"]: log for log in listed.json()}
    assert logs[socel]["name"] == "plant sOCEL"
    assert {"name": "socel", "label": "sOCEL"} in logs[socel]["extensions"]
    assert "socel" not in {entry["name"] for entry in logs[plain_log]["extensions"]}


@pytest.mark.parametrize(
    ("rule", "mutation"),
    [
        ("V1", "DROP TABLE socel_containedin"),
        ("V2", "UPDATE socel_interval_records SET object_id = 'absent' WHERE object_id = 'm1'"),
        (
            "V3",
            "UPDATE socel_event_records SET record_id = "
            "(SELECT min(record_id) FROM socel_interval_records)",
        ),
        ("V4", "UPDATE socel_interval_records SET end_time = start_time WHERE object_id = 'm1'"),
        (
            "V5",
            "ALTER TABLE events ADD COLUMN IF NOT EXISTS socel_end_time TIMESTAMP; "
            'UPDATE events SET socel_end_time = "ocel:timestamp" WHERE "ocel:eid" = \'e1\'',
        ),
        (
            "V6",
            "INSERT INTO socel_interval_records "
            "SELECT 'overlap', flow_id, object_id, quantity, start_time, end_time "
            "FROM socel_interval_records WHERE object_id = 'm1'",
        ),
        (
            "V7",
            "ALTER TABLE events ADD COLUMN IF NOT EXISTS socel_end_time TIMESTAMP; "
            "UPDATE events SET socel_end_time = TIMESTAMP '2026-01-01 11:00:00' "
            "WHERE \"ocel:eid\" = 'e1'; "
            "UPDATE socel_event_records SET flow_id = 'electricity'",
        ),
        ("V8", "UPDATE socel_event_records SET flow_id = 'electricity'"),
        ("V9", "INSERT INTO socel_containedin VALUES ('electricity', 'hall-1', 'm1')"),
        ("V10", "UPDATE socel_flow SET category = 'unknown.category' WHERE flow_id = 'heat'"),
    ],
    ids=[f"V{number}" for number in range(1, 11)],
)
def test_host_recognition_enforces_conformance(
    host: TestClient, session: Session, socel: str, rule: str, mutation: str
) -> None:
    with session.get_ocel(socel, use_original=True) as source, deepcopy(source) as invalid:
        invalid.sql(mutation)
        invalid_id = session.add_ocel(invalid, f"invalid-{rule}")

    assert "socel" not in extension_names(host, invalid_id)
    response = host.get(f"{HOST_SOCEL}/logs/{invalid_id}/summary")
    assert response.status_code == 422, response.text
    assert f"[{rule}]" in response.json()["detail"]
    assert "socel" in extension_names(host, socel)


def test_configuration_preserves_host_recognition(host: TestClient, api: Api, socel: str) -> None:
    assert api.configure_socel(socel, {"activities": {"ship": None}}).status_code == 204
    assert "socel" in extension_names(host, socel)


@pytest.mark.parametrize(
    "extension",
    [
        pytest.param(
            ".json",
            marks=pytest.mark.xfail(
                strict=True,
                raises=AssertionError,
                reason="Host loses JSON extension timestamp types; see library-inventory.md.",
            ),
        ),
        ".xml",
        ".sqlite",
    ],
)
def test_populated_socel_round_trips_through_host_download(
    host: TestClient, api: Api, session: Session, plain_log: str, tmp_path: Path, extension: str
) -> None:
    ocel_id = build(
        api,
        plain_log,
        flows={**FLOWS, "heat": {**FLOWS["heat"], "externalRef": "heat-factor"}},
    )
    upload = api.upload_record_file(ocel_id, b"event,end\ne1,2026-01-01T11:00:00Z\n")
    assert upload.status_code == 201
    configured = api.configure_socel(
        ocel_id,
        {
            "records": {
                "uploadId": upload.json()["uploadId"],
                "mapping": {"event": "event", "endTime": "end"},
            }
        },
    )
    assert configured.status_code == 204, configured.text
    with session.get_ocel(ocel_id, use_original=True) as source:
        expected = snapshot(source)
    assert expected["event_ends"]
    assert ("heat", "kWh", "energy.thermal", "heat-factor") in expected["flows"]

    response = host.get(
        f"{HOST_OCEL}/{ocel_id}/download", params={"ext": extension, "ocel_version": "original"}
    )
    assert response.status_code == 200, response.text
    assert f"plant sOCEL{extension}" in unquote(response.headers["content-disposition"])
    exported = tmp_path / f"populated{extension}"
    exported.write_bytes(response.content)
    imported_id = session.add_ocel_from_file(exported, "round trip")

    assert "socel" in extension_names(host, imported_id), host.get(
        f"{HOST_SOCEL}/logs/{imported_id}/summary"
    ).text
    with session.get_ocel(imported_id, use_original=True) as imported:
        assert snapshot(imported) == expected
    assert api.get_socel_status(imported_id).json() == api.get_socel_status(ocel_id).json()
    assert api.calculate_impact(imported_id, {"heat": {"outflow": 2}}).json() == (
        api.calculate_impact(ocel_id, {"heat": {"outflow": 2}}).json()
    )


@pytest.mark.xfail(
    strict=True,
    raises=AssertionError,
    reason="Pinned host omits empty extension tables on export (see library-inventory.md).",
)
@pytest.mark.parametrize("extension", [".json", ".xml", ".sqlite"])
@pytest.mark.parametrize("records", [False, True], ids=["classification-only", "no-containment"])
def test_socel_with_empty_tables_round_trips_through_host_download(
    host: TestClient,
    api: Api,
    session: Session,
    plain_log: str,
    tmp_path: Path,
    extension: str,
    records: bool,
) -> None:
    if records:
        ocel_id = build(api, plain_log, containment=False)
    else:
        built = api.build_socel(plain_log, {"name": "classified", "activities": {"mill": "op"}})
        assert built.status_code == 201
        ocel_id = built.json()["ocelId"]
    assert "socel" in extension_names(host, ocel_id)
    with session.get_ocel(ocel_id, use_original=True) as source:
        expected = snapshot(source)

    response = host.get(
        f"{HOST_OCEL}/{ocel_id}/download", params={"ext": extension, "ocel_version": "original"}
    )
    assert response.status_code == 200, response.text
    exported = tmp_path / f"sparse{extension}"
    exported.write_bytes(response.content)
    imported_id = session.add_ocel_from_file(exported, "sparse round trip")

    assert "socel" in extension_names(host, imported_id), host.get(
        f"{HOST_SOCEL}/logs/{imported_id}/summary"
    ).text
    with session.get_ocel(imported_id, use_original=True) as imported:
        assert snapshot(imported) == expected
