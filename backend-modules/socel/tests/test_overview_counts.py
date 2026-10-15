"""The counts an sOCEL is summed up by: its flows and its classes."""

from copy import deepcopy

import pytest
from api import Api
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_socel.domain import taxonomies
from ocelescope_module_socel.domain.models.class_taxonomy import ClassNode
from ocelescope_module_socel.infrastructure.adapters.duckdb_socel_statistics import (
    DuckDbSocelStatistics,
)
from ocelescope_module_socel.infrastructure.ocelescope_extension import SOCEL


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


def test_the_class_counts_preserve_full_paths_without_semantic_flags(api: Api, socel: str) -> None:
    counts = api.get_class_counts(socel).json()

    assert counts == {
        "objects": [
            {"socelClass": "hu", "count": 2},
            {"socelClass": "pr.processing.mechanical", "count": 2},
            {"socelClass": "pr.infrastructure", "count": 1},
        ],
        "events": [
            {"socelClass": "op.manufacturing.separating", "count": 2},
            {"socelClass": "op.logistics.transport", "count": 1},
        ],
    }


def test_unclassified_types_are_counted_under_none(api: Api, socel: str) -> None:
    api.configure_socel(socel, {"objectTypes": {"hall": None}})

    objects = api.get_class_counts(socel).json()["objects"]

    assert {"socelClass": None, "count": 1} in objects


def test_class_aggregation_accepts_arbitrary_roots_and_depths(session: Session, socel: str) -> None:
    # Exercise the query independently of the fixed taxonomy's conformance check.
    with session.get_ocel(socel) as source, deepcopy(source) as changed:
        changed.sql("""
            UPDATE object_changes SET socel_class = CASE "ocel:oid"
                WHEN 'm1' THEN 'resources.processing'
                WHEN 'm2' THEN 'resources'
                WHEN 'p1' THEN 'products.component'
                WHEN 'p2' THEN 'products'
                ELSE 'locations.site'
            END WHERE "ocel:field" = 'socel_class';
            UPDATE events SET socel_class = CASE "ocel:eid"
                WHEN 'e1' THEN 'actions.work'
                WHEN 'e2' THEN 'actions.work.drill'
                ELSE NULL
            END;
        """)
        with SOCEL(changed.con.cursor()) as extension:
            counts = DuckDbSocelStatistics(extension).class_counts()

    assert counts.model_dump(mode="json") == {
        "objects": [
            {"socelClass": name, "count": 1}
            for name in (
                "locations.site",
                "products",
                "products.component",
                "resources",
                "resources.processing",
            )
        ],
        "events": [
            {"socelClass": "actions.work", "count": 1},
            {"socelClass": "actions.work.drill", "count": 1},
            {"socelClass": None, "count": 1},
        ],
    }


@pytest.mark.parametrize(
    ("handling_label", "operation_label"),
    [("units", "actions"), ("unit_%'s", "action_%'s")],
)
def test_summary_follows_the_taxonomy_roots(
    session: Session,
    socel: str,
    monkeypatch: pytest.MonkeyPatch,
    handling_label: str,
    operation_label: str,
) -> None:
    assert any(root is taxonomies.HANDLING_UNIT_ROOT for root in taxonomies.TAXONOMY.object_classes)
    assert any(root is taxonomies.OPERATION_ROOT for root in taxonomies.TAXONOMY.event_classes)
    monkeypatch.setattr(taxonomies, "HANDLING_UNIT_ROOT", ClassNode(label=handling_label))
    monkeypatch.setattr(taxonomies, "OPERATION_ROOT", ClassNode(label=operation_label))
    other_handling = handling_label.replace("_", "X").replace("%", "Y")
    other_operation = operation_label.replace("_", "X").replace("%", "Y")
    if other_handling == handling_label:
        other_handling += "extra"
    if other_operation == operation_label:
        other_operation += "extra"

    # Rename the stored assignments too; changing the taxonomy does not migrate log data.
    with session.get_ocel(socel) as source, deepcopy(source) as changed:
        changed.con.execute(
            """
            UPDATE object_changes SET socel_class = CASE "ocel:oid"
                WHEN 'p1' THEN ?
                WHEN 'p2' THEN ?
                WHEN 'm1' THEN ?
                ELSE NULL
            END WHERE "ocel:field" = 'socel_class'
            """,
            [handling_label, f"{handling_label}.child.deep", f"{other_handling}.child"],
        )
        changed.con.execute(
            """
            UPDATE events SET socel_class = CASE "ocel:eid"
                WHEN 'e1' THEN ?
                WHEN 'e2' THEN ?
                ELSE ?
            END
            """,
            [operation_label, f"{operation_label}.child", f"{other_operation}.child"],
        )
        with SOCEL(changed.con.cursor()) as extension:
            status = DuckDbSocelStatistics(extension).status()

    assert (status.handling_units, status.operations) == (2, 2)
    assert (status.objects, status.events) == (5, 3)
