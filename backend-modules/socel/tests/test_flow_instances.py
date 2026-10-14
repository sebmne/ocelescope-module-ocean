"""Pages of the objects a flow is observed at."""

import pytest
from api import Api


def object_ids(page: dict) -> list[str]:
    return [row["objectId"] for row in page["rows"]]


def test_the_largest_quantity_comes_first(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity").json()

    assert page["total"] == 3
    assert object_ids(page) == ["hall-1", "m1", "m2"]
    assert page["rows"][0] == {
        "objectId": "hall-1",
        "objectType": "hall",
        "parentObjectId": None,
        "contains": 2,
        "intervalRecords": 1,
        "eventRecords": 0,
        "quantity": 100.0,
    }
    assert page["path"] == []


def test_pages_are_bounded_and_keep_the_total(api: Api, socel: str) -> None:
    first = api.get_flow_instances(socel, "electricity", limit=2).json()
    second = api.get_flow_instances(socel, "electricity", limit=2, offset=2).json()

    assert object_ids(first) + object_ids(second) == ["hall-1", "m1", "m2"]
    assert (first["total"], second["total"]) == (3, 3)


def test_a_page_beyond_the_last_is_empty(api: Api, socel: str) -> None:
    beyond = api.get_flow_instances(socel, "electricity", limit=2, offset=10).json()

    assert beyond["rows"] == []


@pytest.mark.xfail(
    strict=True,
    reason="Defect: a page beyond the last reports a total of 0, not the 3 matching objects.",
)
def test_a_page_beyond_the_last_keeps_the_total(api: Api, socel: str) -> None:
    beyond = api.get_flow_instances(socel, "electricity", limit=2, offset=10).json()

    assert beyond["total"] == 3


def test_objects_can_be_ordered_by_id(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", order="object").json()

    assert object_ids(page) == ["hall-1", "m1", "m2"]


def test_the_objects_inside_one_come_with_the_way_to_it(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", inside="hall-1").json()

    assert object_ids(page) == ["m1", "m2"]
    assert {row["parentObjectId"] for row in page["rows"]} == {"hall-1"}
    assert page["path"] == ["hall-1"]


def test_objects_can_be_kept_by_type_and_searched(api: Api, socel: str) -> None:
    machines = api.get_flow_instances(socel, "electricity", object_type="machine").json()
    found = api.get_flow_instances(socel, "electricity", search=" m2 ").json()

    assert object_ids(machines) == ["m1", "m2"]
    assert object_ids(found) == ["m2"]


def test_a_flow_without_matches_gives_an_empty_page(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", search="nothing").json()

    assert page == {"total": 0, "rows": [], "path": []}


@pytest.mark.xfail(
    strict=True,
    reason="Current behaviour: an unknown flow gives an empty page (200), the same as a flow "
    "without matches; the plan's contract answers it with 404.",
)
def test_an_unknown_flow_is_not_found(api: Api, socel: str) -> None:
    assert api.get_flow_instances(socel, "steam").status_code == 404
