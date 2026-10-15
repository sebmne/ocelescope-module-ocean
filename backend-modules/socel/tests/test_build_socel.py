"""Building an sOCEL: a new log beside the one it came from."""

import pytest
from api import Api
from conftest import build
from example_log import FLOWS
from ocelescope import EventTypeFilter
from ocelescope_backend.app.internal.session import Session


def test_the_built_log_is_a_new_log_beside_the_source(
    api: Api, session: Session, plain_log: str, socel: str
) -> None:
    assert socel != plain_log
    assert session.ocels[socel].name == "plant sOCEL"
    assert session.ocels[plain_log].name == "plant"
    # The source stays a plain OCEL.
    assert api.get_socel_status(plain_log).status_code == 422


def test_the_built_log_holds_the_classes_records_and_containment(api: Api, socel: str) -> None:
    status = api.get_socel_status(socel).json()

    assert status == {
        "objects": 5,
        "events": 3,
        "handlingUnits": 2,
        "operations": 3,
        "flows": 2,
        "flowInstances": 4,
        "intervalRecords": 3,
        "eventRecords": 1,
        "containments": 2,
        "recordsFrom": "2026-01-01T00:00:00",
        "recordsTo": "2026-01-03T00:00:00",
    }


def test_the_built_log_is_classified_per_type(api: Api, socel: str) -> None:
    classification = api.get_log_classification(socel).json()

    assert classification == {
        "activities": [
            {"name": "mill", "count": 2, "socelClass": "op.manufacturing.separating"},
            {"name": "ship", "count": 1, "socelClass": "op.logistics.transport"},
        ],
        "objectTypes": [
            {"name": "machine", "count": 2, "socelClass": "pr.processing.mechanical"},
            {"name": "part", "count": 2, "socelClass": "hu"},
            {"name": "hall", "count": 1, "socelClass": "pr.infrastructure"},
        ],
    }


def test_event_attributes_become_event_linked_records(api: Api, plain_log: str) -> None:
    built = build(
        api,
        plain_log,
        attributeFlows=[
            {
                "attribute": "coolant_l",
                "flowId": "coolant",
                "objectType": "machine",
                "direction": "out",
            }
        ],
        flows={**FLOWS, "coolant": {"unit": "l", "category": "material.auxiliary"}},
    )

    report = api.calculate_impact(built, {"coolant": {"outflow": 1.0}}).json()

    coolant = next(flow for flow in report["flows"] if flow["flowId"] == "coolant")
    # 2 l at e1 (m1, 1 January) and 3 l at e2 (m2, 2 January), out of the machines.
    assert (coolant["inflow"], coolant["outflow"]) == (0.0, 5.0)
    assert [part["impact"] for part in report["byPeriod"]] == [2.0, 3.0]


def test_the_build_reads_the_log_through_the_apps_filters(
    api: Api, session: Session, plain_log: str
) -> None:
    session.set_filter(plain_log, "test", [EventTypeFilter(event_types=["ship"])])

    built = build(api, plain_log, activities={"mill": "op.manufacturing.separating"})

    activities = api.get_log_classification(built).json()["activities"]
    assert [activity["name"] for activity in activities] == ["mill"]


def test_an_activity_the_log_does_not_have_is_refused(api: Api, plain_log: str) -> None:
    response = api.build_socel(plain_log, {"name": "x", "activities": {"weld": "op"}})

    assert response.status_code == 422
    assert response.json() == {"detail": "The log has no activity 'weld'."}


def test_a_class_outside_the_taxonomy_is_refused(api: Api, plain_log: str) -> None:
    response = api.build_socel(plain_log, {"name": "x", "objectTypes": {"part": "widget"}})

    assert response.status_code == 422
    assert response.json() == {"detail": "'widget' is no object type class of the taxonomy."}


def test_a_flow_without_definition_is_refused(api: Api, plain_log: str) -> None:
    response = api.build_socel(
        plain_log,
        {
            "name": "x",
            "attributeFlows": [
                {"attribute": "coolant_l", "flowId": "coolant", "objectType": "machine"}
            ],
        },
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "The flow 'coolant' needs a unit and a category."}


def test_a_refused_build_adds_no_log(api: Api, session: Session, plain_log: str) -> None:
    api.build_socel(plain_log, {"name": "x", "activities": {"weld": "op"}})

    assert list(session.ocels) == [plain_log]


def test_a_missing_log_is_not_found(api: Api) -> None:
    assert api.build_socel("missing", {"name": "x"}).status_code == 404


def test_a_created_log_returns_a_readable_location(api: Api, plain_log: str) -> None:
    response = api.build_socel(plain_log, {"name": "new sOCEL"})
    assert response.status_code == 201
    assert response.headers["location"].endswith(f"/logs/{response.json()['ocelId']}/summary")
    assert api.get_socel_status(response.json()["ocelId"]).status_code == 200


def test_new_log_names_are_trimmed_at_the_http_boundary(
    api: Api, session: Session, plain_log: str
) -> None:
    response = api.build_socel(plain_log, {"name": "  prepared plant  "})
    assert response.status_code == 201
    assert session.ocels[response.json()["ocelId"]].name == "prepared plant"


@pytest.mark.parametrize("name", ["", "  "])
def test_blank_new_log_names_are_refused_without_publishing(
    api: Api, session: Session, plain_log: str, name: str
) -> None:
    before = set(session.ocels)
    assert api.build_socel(plain_log, {"name": name}).status_code == 422
    assert set(session.ocels) == before
