"""What a plain OCEL, one that is no sOCEL, can and cannot be asked."""

import pytest
from api import Api


def test_a_plain_log_can_be_asked_for_its_classification(api: Api, plain_log: str) -> None:
    classification = api.get_log_classification(plain_log).json()

    assert classification == {
        "activities": [
            {"name": "mill", "count": 2, "socelClass": None},
            {"name": "ship", "count": 1, "socelClass": None},
        ],
        "objectTypes": [
            {"name": "machine", "count": 2, "socelClass": None},
            {"name": "part", "count": 2, "socelClass": None},
            {"name": "hall", "count": 1, "socelClass": None},
        ],
    }


@pytest.mark.parametrize(
    "ask",
    [
        lambda api, log: api.get_socel_status(log),
        lambda api, log: api.get_class_counts(log),
        lambda api, log: api.get_flow_inventory(log),
        lambda api, log: api.get_flow_instances(log, "electricity"),
        lambda api, log: api.calculate_impact(log, {}),
    ],
    ids=["status", "class counts", "flows", "flow instances", "impact"],
)
def test_sOCEL_questions_are_refused_with_the_reason(api: Api, plain_log: str, ask) -> None:
    response = ask(api, plain_log)

    assert response.status_code == 422
    assert "[V1] Required table 'socel_flow' is missing." in response.json()["detail"]


def test_a_missing_log_is_not_found(api: Api) -> None:
    assert api.get_socel_status("missing").status_code == 404
    assert api.get_log_classification("missing").status_code == 404
