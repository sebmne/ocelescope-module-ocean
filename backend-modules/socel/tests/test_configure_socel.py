"""Configuring an sOCEL: the log is changed in place."""

from api import Api
from ocelescope import EventTypeFilter
from ocelescope_backend.app.internal.session import Session


def test_the_log_keeps_its_id_and_name(api: Api, session: Session, socel: str) -> None:
    logs = set(session.ocels)

    response = api.configure_socel(socel, {"activities": {"ship": "op.logistics.storage"}})

    assert response.status_code == 204
    assert response.content == b""
    assert set(session.ocels) == logs
    assert session.ocels[socel].name == "plant sOCEL"
    activities = api.get_log_classification(socel).json()["activities"]
    assert {a["name"]: a["socelClass"] for a in activities}["ship"] == "op.logistics.storage"


def test_types_not_named_keep_their_class(api: Api, socel: str) -> None:
    api.configure_socel(socel, {"objectTypes": {"hall": None}})

    object_types = api.get_log_classification(socel).json()["objectTypes"]
    assert {t["name"]: t["socelClass"] for t in object_types} == {
        "machine": "pr.processing.mechanical",
        "part": "hu",
        "hall": None,
    }


def test_the_whole_log_is_changed_not_what_the_filters_show(
    api: Api, session: Session, socel: str
) -> None:
    session.set_filter(socel, "test", [EventTypeFilter(event_types=["ship"])])

    response = api.configure_socel(socel, {"activities": {"ship": "op.logistics.storage"}})

    assert response.status_code == 204
    original = api.get_log_classification(socel, original=True).json()["activities"]
    assert {a["name"]: a["socelClass"] for a in original}["ship"] == "op.logistics.storage"
    filtered = api.get_log_classification(socel).json()["activities"]
    assert [a["name"] for a in filtered] == ["mill"]


def test_the_records_stay_when_only_classes_change(api: Api, socel: str) -> None:
    before = api.get_socel_status(socel).json()

    api.configure_socel(socel, {"activities": {"ship": "op.logistics.storage"}})

    assert api.get_socel_status(socel).json() == before


def test_a_refused_change_leaves_the_log_as_it_was(api: Api, socel: str) -> None:
    before = api.get_flow_inventory(socel).json()

    response = api.configure_socel(socel, {"activities": {"ship": "nonsense"}})

    assert response.status_code == 422
    assert api.get_flow_inventory(socel).json() == before


def test_a_change_that_breaks_conformance_leaves_the_log_as_it_was(api: Api, socel: str) -> None:
    """The change passes the checks before writing, then fails the sOCEL rules
    on the changed copy: a flow without category (V10)."""
    before = api.get_flow_inventory(socel).json()

    response = api.configure_socel(
        socel,
        {"flowEdits": [{"flowId": "heat", "name": "heat", "unit": "kWh", "category": None}]},
    )

    assert response.status_code == 422
    assert "[V10]" in response.json()["detail"]
    assert api.get_flow_inventory(socel).json() == before


def test_a_missing_log_is_not_found(api: Api) -> None:
    assert api.configure_socel("missing", {}).status_code == 404
