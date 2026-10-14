import shutil
from collections.abc import Iterator
from typing import Any

import pytest
from api import Api
from example_log import CLASSES, CONTAINMENT, FLOWS, MAPPING, RECORDS_CSV, example_log
from fastapi.testclient import TestClient
from ocelescope_backend.app.dependencies import get_session
from ocelescope_backend.app.internal.session import Session
from ocelescope_backend.app.modules.loader import build_module

from ocelescope_module_socel.module import Socel


@pytest.fixture
def session() -> Iterator[Session]:
    """A real Ocelescope session; its logs are DuckDB files in a temporary folder."""
    session = Session()
    yield session
    for ocel_id in list(session.ocels):
        session.delete_ocel(ocel_id)
    Session.sessions.pop(session.id, None)
    shutil.rmtree(session._ocel_dir, ignore_errors=True)  # pyright: ignore[reportPrivateUsage]


@pytest.fixture
def api(session: Session) -> Iterator[Api]:
    """The module's app as the host mounts it, with every request in `session`."""
    app = build_module(Socel).create_app()
    app.dependency_overrides[get_session] = lambda: session
    with TestClient(app) as client:
        yield Api(client)


@pytest.fixture
def plain_log(session: Session) -> str:
    """The id of the example log, a plain OCEL."""
    return session.add_ocel(example_log(), "plant")


def build(api: Api, ocel_id: str, *, containment: bool = True, **changes: Any) -> str:
    """Builds an sOCEL from the log with the example records; returns its id."""
    upload = api.upload_record_file(ocel_id, RECORDS_CSV)
    assert upload.status_code == 200, upload.text
    body = {
        "name": "plant sOCEL",
        **CLASSES,
        "flows": FLOWS,
        "records": {"uploadId": upload.json()["uploadId"], "mapping": MAPPING},
        "containment": CONTAINMENT if containment else [],
        **changes,
    }
    built = api.build_socel(ocel_id, body)
    assert built.status_code == 200, built.text
    return built.json()["ocelId"]


@pytest.fixture
def socel(api: Api, plain_log: str) -> str:
    """The id of the example log built into an sOCEL, with containment."""
    return build(api, plain_log)
