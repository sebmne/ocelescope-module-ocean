import unittest
from datetime import UTC, datetime

from test_validation import add_extension_tables, make_ocel

from socel import SOCEL, EventRecord, Flow, FlowInstance, IntervalRecord


def add_domain_data(ocel) -> None:
    ocel.con.execute("INSERT INTO objects VALUES ('factory-1', 'factory')")
    ocel.con.executemany(
        "INSERT INTO socel_flow VALUES (?, ?, ?, ?)",
        [
            ("electricity", "kWh", "energy", None),
            ("water", "l", "material", "https://example.test/water"),
        ],
    )
    ocel.con.execute(
        "INSERT INTO socel_interval_records VALUES (?, ?, ?, ?, ?, ?)",
        [
            "interval-1",
            "electricity",
            "machine-1",
            1.5,
            datetime(2026, 1, 1, 10, tzinfo=UTC),
            datetime(2026, 1, 1, 11, tzinfo=UTC),
        ],
    )
    ocel.con.execute(
        "INSERT INTO socel_event_records VALUES (?, ?, ?, ?, ?)",
        ["event-record-1", "water", "machine-1", 2.0, "event-1"],
    )
    ocel.con.execute(
        "INSERT INTO socel_containedin VALUES (?, ?, ?)",
        ["electricity", "machine-1", "factory-1"],
    )


def add_classifications(ocel) -> None:
    ocel.con.execute("ALTER TABLE events ADD COLUMN socel_class VARCHAR")
    ocel.con.execute(
        "UPDATE events SET socel_class = 'op.manufacturing.forming' "
        "WHERE \"ocel:eid\" = 'event-1'"
    )
    ocel.con.execute("ALTER TABLE object_changes ADD COLUMN socel_class VARCHAR")
    ocel.con.execute(
        """
        INSERT INTO object_changes BY NAME
        SELECT
            'machine-1' AS "ocel:oid",
            TIMESTAMP '1970-01-01' AS "ocel:timestamp",
            'socel_class' AS "ocel:field",
            'pr.processing.mechanical' AS socel_class
        """
    )


class DomainManagerTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ocel = make_ocel()
        add_extension_tables(self.ocel)
        add_domain_data(self.ocel)

    def tearDown(self) -> None:
        self.ocel.close()

    def test_flows_return_domain_objects(self) -> None:
        socel = SOCEL.from_ocel(self.ocel)

        self.assertEqual(
            socel.flows.get("electricity"),
            Flow(id="electricity", unit="kWh", category="energy"),
        )
        self.assertEqual(
            tuple(flow.id for flow in socel.flows.by_category("material")),
            ("water",),
        )
        self.assertIsNone(socel.flows.get("unknown"))

    def test_flow_instances_are_derived_from_records_and_containment(self) -> None:
        socel = SOCEL.from_ocel(self.ocel)
        machine_electricity = FlowInstance("machine-1", "electricity")
        factory_electricity = FlowInstance("factory-1", "electricity")

        self.assertEqual(
            socel.flow_instances.get("machine-1", "electricity"),
            machine_electricity,
        )
        self.assertEqual(
            socel.flow_instances.parent(machine_electricity),
            factory_electricity,
        )
        self.assertEqual(
            socel.flow_instances.children(factory_electricity),
            (machine_electricity,),
        )
        self.assertEqual(
            socel.flow_instances.roots("electricity"),
            (factory_electricity,),
        )

    def test_measurements_unify_interval_and_event_records(self) -> None:
        socel = SOCEL.from_ocel(self.ocel)

        records = socel.measurements.all()

        self.assertEqual(len(records), 2)
        self.assertIsInstance(records[0], EventRecord)
        self.assertIsInstance(records[1], IntervalRecord)
        self.assertEqual(
            socel.measurements.for_event("event-1"),
            (records[0],),
        )
        self.assertEqual(
            socel.measurements.for_instance(FlowInstance("machine-1", "electricity")),
            (records[1],),
        )

    def test_classifications_interpret_reserved_attributes(self) -> None:
        add_classifications(self.ocel)
        socel = SOCEL.from_ocel(self.ocel)

        self.assertEqual(
            socel.classifications.object_class("machine-1"),
            "pr.processing.mechanical",
        )
        self.assertEqual(
            socel.classifications.event_class("event-1"),
            "op.manufacturing.forming",
        )
        self.assertEqual(
            tuple(
                item.element_id for item in socel.classifications.process_resources()
            ),
            ("machine-1",),
        )
        self.assertEqual(
            tuple(item.element_id for item in socel.classifications.operations()),
            ("event-1",),
        )

    def test_managers_read_current_ocel_state(self) -> None:
        socel = SOCEL.from_ocel(self.ocel)
        self.ocel.con.execute(
            "INSERT INTO socel_flow VALUES ('gas', 'm3', 'energy', NULL)"
        )

        self.assertEqual(socel.flows.get("gas"), Flow("gas", "m3", "energy"))


if __name__ == "__main__":
    unittest.main()
