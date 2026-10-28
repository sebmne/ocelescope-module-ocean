"""Pages of a flow's records at one object."""

from copy import deepcopy

from api import Api
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_socel.infrastructure.adapters.duckdb_socel_statistics import (
    DuckDbSocelStatistics,
)
from ocelescope_module_socel.infrastructure.ocelescope_extension import SOCEL


def without_ids(page: dict) -> list[dict]:
    return [{k: v for k, v in row.items() if k != "recordId"} for row in page["items"]]


def test_an_interval_record_comes_with_its_start_and_end(api: Api, socel: str) -> None:
    page = api.get_flow_records(socel, "electricity", object_id="m1").json()

    assert page["total"] == 1
    assert without_ids(page) == [
        {
            "kind": "interval",
            "quantity": 24.0,
            "start": "2026-01-01T00:00:00",
            "end": "2026-01-02T00:00:00",
            "eventId": None,
            "activity": None,
        }
    ]


def test_an_event_linked_record_comes_with_its_event(api: Api, socel: str) -> None:
    page = api.get_flow_records(socel, "heat", object_id="m1").json()

    assert without_ids(page) == [
        {
            "kind": "event",
            "quantity": -5.0,
            "start": "2026-01-01T10:00:00",
            "end": None,
            "eventId": "e1",
            "activity": "mill",
        }
    ]


def test_an_event_linked_record_ends_with_its_event(session: Session, socel: str) -> None:
    with session.get_ocel(socel) as source, deepcopy(source) as changed:
        changed.sql("""
            ALTER TABLE events ADD COLUMN IF NOT EXISTS socel_end_time TIMESTAMP;
            UPDATE events SET socel_end_time = TIMESTAMP '2026-01-01 11:30:00'
            WHERE "ocel:eid" = 'e1';
        """)
        with SOCEL(changed.con.cursor()) as extension:
            records, _ = DuckDbSocelStatistics(extension).flow_records(
                "heat", "m1", offset=0, limit=10
            )

    assert [record.end.isoformat() if record.end else None for record in records] == [
        "2026-01-01T11:30:00"
    ]


def test_an_object_without_records_has_none(api: Api, socel: str) -> None:
    page = api.get_flow_records(socel, "heat", object_id="m2").json()

    assert (page["items"], page["total"]) == ([], 0)


def test_pages_are_bounded_and_keep_the_total(api: Api, socel: str) -> None:
    beyond = api.get_flow_records(socel, "electricity", object_id="m1", offset=5).json()

    assert (beyond["items"], beyond["total"]) == ([], 1)


def test_records_of_a_missing_flow_are_not_found(api: Api, socel: str) -> None:
    response = api.get_flow_records(socel, "steam", object_id="m1")

    assert response.status_code == 404
