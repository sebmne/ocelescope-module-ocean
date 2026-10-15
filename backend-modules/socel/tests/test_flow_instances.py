"""Pages of the objects a flow is observed at."""

import pytest
from api import Api


def object_ids(page: dict) -> list[str]:
    return [row["objectId"] for row in page["items"]]


def test_the_largest_quantity_comes_first(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity").json()

    assert page["total"] == 3
    assert object_ids(page) == ["hall-1", "m1", "m2"]
    assert page["items"][0] == {
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

    assert beyond["items"] == []


def test_a_page_beyond_the_last_keeps_the_total(api: Api, socel: str) -> None:
    beyond = api.get_flow_instances(socel, "electricity", limit=2, offset=10).json()

    assert beyond["total"] == 3


def test_objects_can_be_ordered_by_id(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", order="object").json()

    assert object_ids(page) == ["hall-1", "m1", "m2"]


def test_the_objects_inside_one_come_with_the_way_to_it(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", inside="hall-1").json()

    assert object_ids(page) == ["m1", "m2"]
    assert {row["parentObjectId"] for row in page["items"]} == {"hall-1"}
    assert page["path"] == ["hall-1"]


def test_objects_can_be_kept_by_type_and_searched(api: Api, socel: str) -> None:
    machines = api.get_flow_instances(socel, "electricity", object_type="machine").json()
    found = api.get_flow_instances(socel, "electricity", search=" m2 ").json()

    assert object_ids(machines) == ["m1", "m2"]
    assert object_ids(found) == ["m2"]


def test_a_flow_without_matches_gives_an_empty_page(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", search="nothing").json()

    assert page == {"items": [], "total": 0, "offset": 0, "limit": 50, "path": []}


def test_an_unknown_flow_is_not_found(api: Api, socel: str) -> None:
    assert api.get_flow_instances(socel, "steam").status_code == 404


@pytest.mark.parametrize(
    "params",
    [
        {"offset": -1},
        {"limit": 0},
        {"limit": 201},
        {"offset": "invalid"},
        {"order": "invalid"},
    ],
)
def test_invalid_pagination_or_order_returns_422(api: Api, socel: str, params: dict) -> None:
    assert api.get_flow_instances(socel, "electricity", **params).status_code == 422


def test_page_metadata_reports_the_requested_range(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", offset=1, limit=1).json()
    assert (page["offset"], page["limit"], page["total"]) == (1, 1, 3)
    assert object_ids(page) == ["m1"]


def test_totals_beyond_the_end_apply_the_same_filters(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", search="m1", offset=10, limit=2).json()
    assert page == {"items": [], "total": 1, "offset": 10, "limit": 2, "path": []}


def test_empty_containment_pages_keep_their_breadcrumbs(api: Api, socel: str) -> None:
    page = api.get_flow_instances(socel, "electricity", inside="hall-1", offset=10, limit=2).json()
    assert page == {"items": [], "total": 2, "offset": 10, "limit": 2, "path": ["hall-1"]}
