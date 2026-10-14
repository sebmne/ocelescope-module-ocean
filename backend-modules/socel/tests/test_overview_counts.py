"""The counts an sOCEL is summed up by: its flows and its classes."""

from api import Api


def test_the_flow_inventory_counts_per_flow_and_object_type(api: Api, socel: str) -> None:
    inventory = api.get_flow_inventory(socel).json()

    assert inventory == [
        {
            "flowId": "electricity",
            "unit": "kWh",
            "category": "energy.electricity",
            "externalRef": None,
            "instances": 3,
            "contained": 2,
            "intervalRecords": 3,
            "eventRecords": 0,
            "byObjectType": [
                {
                    "objectType": "machine",
                    "instances": 2,
                    "contained": 2,
                    "intervalRecords": 2,
                    "eventRecords": 0,
                },
                {
                    "objectType": "hall",
                    "instances": 1,
                    "contained": 0,
                    "intervalRecords": 1,
                    "eventRecords": 0,
                },
            ],
        },
        {
            "flowId": "heat",
            "unit": "kWh",
            "category": "energy.thermal",
            "externalRef": None,
            "instances": 1,
            "contained": 0,
            "intervalRecords": 0,
            "eventRecords": 1,
            "byObjectType": [
                {
                    "objectType": "machine",
                    "instances": 1,
                    "contained": 0,
                    "intervalRecords": 0,
                    "eventRecords": 1,
                }
            ],
        },
    ]


def test_the_class_counts_mark_the_core_classes(api: Api, socel: str) -> None:
    counts = api.get_class_counts(socel).json()

    assert counts == {
        "objects": [
            {"socelClass": "hu", "count": 2, "isCore": True},
            {"socelClass": "pr.processing.mechanical", "count": 2, "isCore": False},
            {"socelClass": "pr.infrastructure", "count": 1, "isCore": False},
        ],
        "events": [
            {"socelClass": "op.manufacturing.separating", "count": 2, "isCore": True},
            {"socelClass": "op.logistics.transport", "count": 1, "isCore": True},
        ],
    }


def test_unclassified_types_are_counted_under_none(api: Api, socel: str) -> None:
    api.configure_socel(socel, {"objectTypes": {"hall": None}})

    objects = api.get_class_counts(socel).json()["objects"]

    assert {"socelClass": None, "count": 1, "isCore": False} in objects
