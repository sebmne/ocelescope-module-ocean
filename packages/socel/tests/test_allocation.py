import unittest

from test_validation import add_extension_tables, make_ocel

from socel import SOCEL, FlowInstance
from socel.analysis import (
    AllocationParameters,
    AllocationResult,
    AttributionScope,
    FlowAllocation,
    FlowSelection,
    HandlingUnitQuantity,
    LineageDefinition,
    allocate,
    carry,
    event_quantities,
)


class AllocationParameterTests(unittest.TestCase):
    def test_selection_rejects_empty_identifiers(self) -> None:
        with self.assertRaisesRegex(ValueError, "non-empty identifiers"):
            FlowSelection(frozenset({FlowInstance("", "electricity")}))

    def test_parameters_reject_duplicate_scopes(self) -> None:
        instance = FlowInstance("machine-1", "electricity")
        scope = AttributionScope(instance)

        with self.assertRaisesRegex(ValueError, "one attribution scope"):
            AllocationParameters(
                FlowSelection(frozenset({instance})),
                (scope, scope),
            )

    def test_parameters_reject_scope_outside_selection(self) -> None:
        with self.assertRaisesRegex(ValueError, "belong to the flow selection"):
            AllocationParameters(
                FlowSelection(frozenset({FlowInstance("machine-1", "electricity")})),
                (AttributionScope(FlowInstance("machine-2", "electricity")),),
            )

    def test_allocation_requires_quantity_conservation(self) -> None:
        with self.assertRaisesRegex(ValueError, "must reconcile"):
            FlowAllocation(
                flow_id="electricity",
                handling_units=(HandlingUnitQuantity("product-1", 3.0),),
                unallocated=1.0,
                recorded=5.0,
            )

    def test_lineage_definition_requires_parameter_names(self) -> None:
        with self.assertRaisesRegex(ValueError, "qualifier"):
            LineageDefinition("", "mass")
        with self.assertRaisesRegex(ValueError, "mass attribute"):
            LineageDefinition("created from", "")


class AllocationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ocel = make_ocel()
        add_extension_tables(self.ocel)
        self.ocel.con.execute("ALTER TABLE events ADD COLUMN socel_class VARCHAR")
        self.ocel.con.execute(
            "UPDATE events SET socel_class = 'op.manufacturing.forming'"
        )
        self.ocel.con.execute(
            "ALTER TABLE object_changes ADD COLUMN socel_class VARCHAR"
        )
        self.ocel.con.execute("ALTER TABLE object_changes ADD COLUMN mass DOUBLE")
        self.ocel.con.execute(
            "INSERT INTO socel_flow VALUES "
            "('electricity', 'kWh', 'energy.electricity', NULL)"
        )

    def tearDown(self) -> None:
        self.ocel.close()

    def test_event_quantities_sum_selected_instances_per_flow(self) -> None:
        self._add_object("machine-2", "machine")
        self.ocel.con.execute(
            "INSERT INTO e2o VALUES ('event-1', 'resource', 'machine-2')"
        )
        self._add_event_record("record-1", "machine-1", 4.0)
        self._add_event_record("record-2", "machine-2", 6.0)
        socel = SOCEL.from_ocel(self.ocel)

        quantities = event_quantities(
            socel,
            AllocationParameters(
                FlowSelection(
                    frozenset(
                        {
                            FlowInstance("machine-1", "electricity"),
                            FlowInstance("machine-2", "electricity"),
                        }
                    )
                )
            ),
        )

        self.assertEqual(len(quantities), 1)
        self.assertEqual(quantities[0].flow_id, "electricity")
        self.assertEqual(quantities[0].event_id, "event-1")
        self.assertEqual(quantities[0].quantity, 10.0)

    def test_selection_rejects_nested_reporting_scopes(self) -> None:
        self._add_object("line-1", "line")
        self._add_event_record("record-1", "machine-1", 4.0)
        self._add_event_record("record-2", "line-1", 6.0)
        self.ocel.con.execute(
            "INSERT INTO socel_containedin VALUES "
            "('electricity', 'machine-1', 'line-1')"
        )
        socel = SOCEL.from_ocel(self.ocel)
        selection = FlowSelection(
            frozenset(
                {
                    FlowInstance("machine-1", "electricity"),
                    FlowInstance("line-1", "electricity"),
                }
            )
        )

        with self.assertRaisesRegex(ValueError, "nested instances"):
            selection.validate_for(socel)

    def test_allocation_divides_event_quantity_equally_between_handling_units(
        self,
    ) -> None:
        self._add_handling_unit("product-1", 1.0)
        self._add_handling_unit("product-2", 1.0)
        self._relate_to_event("product-1")
        self._relate_to_event("product-2")
        self._add_event_record("record-1", "machine-1", 10.0)
        socel = SOCEL.from_ocel(self.ocel)

        result = allocate(socel, self._machine_parameters())

        flow = result.for_flow("electricity")
        self.assertIsNotNone(flow)
        assert flow is not None
        self.assertEqual(flow.for_handling_unit("product-1"), 5.0)
        self.assertEqual(flow.for_handling_unit("product-2"), 5.0)
        self.assertEqual(flow.unallocated, 0.0)
        self.assertEqual(flow.recorded, 10.0)

    def test_quantity_without_participating_handling_unit_remains_unallocated(
        self,
    ) -> None:
        self._add_event_record("record-1", "machine-1", 10.0)
        socel = SOCEL.from_ocel(self.ocel)

        result = allocate(socel, self._machine_parameters())

        flow = result.for_flow("electricity")
        self.assertIsNotNone(flow)
        assert flow is not None
        self.assertEqual(flow.handling_units, ())
        self.assertEqual(flow.unallocated, 10.0)

    def test_carry_propagates_parent_quantity_by_child_mass_share(self) -> None:
        self._add_handling_unit("parent", 4.0)
        self._add_handling_unit("child-1", 1.0)
        self._add_handling_unit("child-2", 3.0)
        self._add_creation_relation("child-1", "parent")
        self._add_creation_relation("child-2", "parent")
        socel = SOCEL.from_ocel(self.ocel)
        allocation = AllocationResult(
            (
                FlowAllocation(
                    flow_id="electricity",
                    handling_units=(
                        HandlingUnitQuantity("parent", 40.0),
                        HandlingUnitQuantity("child-1", 2.0),
                        HandlingUnitQuantity("child-2", 3.0),
                    ),
                    unallocated=5.0,
                    recorded=50.0,
                ),
            )
        )

        result = carry(
            socel,
            allocation,
            LineageDefinition("created from", "mass"),
        )

        flow = result.for_flow("electricity")
        self.assertIsNotNone(flow)
        assert flow is not None
        self.assertEqual(flow.for_handling_unit("parent"), 40.0)
        self.assertEqual(flow.for_handling_unit("child-1"), 12.0)
        self.assertEqual(flow.for_handling_unit("child-2"), 33.0)
        self.assertEqual(flow.unallocated, 5.0)

    def _machine_parameters(self) -> AllocationParameters:
        return AllocationParameters(
            FlowSelection(frozenset({FlowInstance("machine-1", "electricity")}))
        )

    def _add_event_record(
        self,
        record_id: str,
        object_id: str,
        quantity: float,
    ) -> None:
        self.ocel.con.execute(
            "INSERT INTO socel_event_records VALUES (?, ?, ?, ?, 'event-1')",
            [record_id, "electricity", object_id, quantity],
        )

    def _add_object(self, object_id: str, object_type: str) -> None:
        self.ocel.con.execute(
            "INSERT INTO objects VALUES (?, ?)",
            [object_id, object_type],
        )

    def _add_handling_unit(self, object_id: str, mass: float) -> None:
        self._add_object(object_id, "product")
        self.ocel.con.execute(
            """
            INSERT INTO object_changes BY NAME
            SELECT
                ? AS "ocel:oid",
                TIMESTAMP '1970-01-01' AS "ocel:timestamp",
                'socel_class' AS "ocel:field",
                'hu' AS socel_class
            """,
            [object_id],
        )
        self.ocel.con.execute(
            """
            INSERT INTO object_changes BY NAME
            SELECT
                ? AS "ocel:oid",
                TIMESTAMP '1970-01-01' AS "ocel:timestamp",
                'mass' AS "ocel:field",
                ? AS mass
            """,
            [object_id, mass],
        )

    def _relate_to_event(self, object_id: str) -> None:
        self.ocel.con.execute(
            "INSERT INTO e2o VALUES ('event-1', 'target', ?)",
            [object_id],
        )

    def _add_creation_relation(self, child: str, parent: str) -> None:
        self.ocel.con.execute(
            "INSERT INTO o2o VALUES (?, ?, 'created from')",
            [child, parent],
        )


if __name__ == "__main__":
    unittest.main()
