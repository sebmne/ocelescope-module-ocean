import unittest
from datetime import UTC, datetime

from test_validation import add_extension_tables, make_ocel

from socel import SOCEL, FlowInstance
from socel.analysis import (
    AttributionResult,
    AttributionScope,
    EventAttribution,
    attribute,
)


def timestamp(hour: int, minute: int = 0) -> datetime:
    """Match the timezone-naive timestamps returned by DuckDB ``TIMESTAMP``."""
    return datetime(2026, 1, 1, hour, minute, tzinfo=UTC).replace(tzinfo=None)


class AttributionParameterTests(unittest.TestCase):
    def test_scope_rejects_empty_operation_identifiers(self) -> None:
        with self.assertRaisesRegex(ValueError, "must not be empty"):
            AttributionScope(
                FlowInstance("machine-1", "electricity"),
                frozenset({""}),
            )

    def test_result_requires_quantity_conservation(self) -> None:
        with self.assertRaisesRegex(ValueError, "must reconcile"):
            AttributionResult(
                events=(EventAttribution("event-1", 3.0),),
                unattributed=1.0,
                recorded=5.0,
            )

    def test_scope_rejects_two_operation_selection_strategies(self) -> None:
        with self.assertRaisesRegex(ValueError, "cannot be combined"):
            AttributionScope(
                FlowInstance("machine-1", "electricity"),
                eligible_operations=frozenset({"event-1"}),
                include_contained_operations=True,
            )


class AttributionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ocel = make_ocel()
        add_extension_tables(self.ocel)
        self.ocel.con.execute("ALTER TABLE events ADD COLUMN socel_class VARCHAR")
        self.ocel.con.execute("ALTER TABLE events ADD COLUMN socel_end_time TIMESTAMP")
        self.ocel.con.execute(
            "INSERT INTO socel_flow VALUES "
            "('electricity', 'kWh', 'energy.electricity', NULL)"
        )

    def tearDown(self) -> None:
        self.ocel.close()

    def test_overlapping_operations_split_interval_shares_equally(self) -> None:
        self._configure_event("event-1", timestamp(10), timestamp(11))
        self._add_event("event-2", timestamp(10, 30), timestamp(11, 30))
        self._add_interval("machine-1", 90.0, timestamp(10), timestamp(11, 30))
        socel = SOCEL.from_ocel(self.ocel)

        result = attribute(
            socel,
            AttributionScope(FlowInstance("machine-1", "electricity")),
        )

        self.assertEqual(result.for_event("event-1"), 45.0)
        self.assertEqual(result.for_event("event-2"), 45.0)
        self.assertEqual(result.unattributed, 0.0)
        self.assertEqual(result.recorded, 90.0)

    def test_quantity_outside_operation_windows_remains_unattributed(self) -> None:
        self._configure_event("event-1", timestamp(10), timestamp(11))
        self._add_interval("machine-1", 120.0, timestamp(9, 30), timestamp(11, 30))
        socel = SOCEL.from_ocel(self.ocel)

        result = attribute(
            socel,
            AttributionScope(FlowInstance("machine-1", "electricity")),
        )

        self.assertEqual(result.for_event("event-1"), 60.0)
        self.assertEqual(result.unattributed, 60.0)

    def test_event_linked_record_is_assigned_without_event_duration(self) -> None:
        self._configure_event("event-1", timestamp(10), None)
        self.ocel.con.execute(
            "INSERT INTO socel_event_records VALUES "
            "('record-1', 'electricity', 'machine-1', 7.0, 'event-1')"
        )
        socel = SOCEL.from_ocel(self.ocel)

        result = attribute(
            socel,
            AttributionScope(FlowInstance("machine-1", "electricity")),
        )

        self.assertEqual(result.for_event("event-1"), 7.0)
        self.assertEqual(result.unattributed, 0.0)

    def test_explicit_eligible_operations_override_the_default(self) -> None:
        self._configure_event("event-1", timestamp(10), timestamp(11))
        self._add_event("event-2", timestamp(10), timestamp(11))
        self._add_interval("machine-1", 10.0, timestamp(10), timestamp(11))
        socel = SOCEL.from_ocel(self.ocel)

        result = attribute(
            socel,
            AttributionScope(
                FlowInstance("machine-1", "electricity"),
                eligible_operations=frozenset({"event-2"}),
            ),
        )

        self.assertEqual(result.for_event("event-1"), 0.0)
        self.assertEqual(result.for_event("event-2"), 10.0)

    def test_group_metering_uses_operations_of_contained_instances(self) -> None:
        self._configure_event("event-1", timestamp(10), timestamp(11))
        self.ocel.con.execute("INSERT INTO objects VALUES ('line-1', 'line')")
        self.ocel.con.execute(
            "INSERT INTO socel_containedin VALUES "
            "('electricity', 'machine-1', 'line-1')"
        )
        self._add_interval("line-1", 12.0, timestamp(10), timestamp(11))
        socel = SOCEL.from_ocel(self.ocel)

        default_result = attribute(
            socel,
            AttributionScope(FlowInstance("line-1", "electricity")),
        )
        result = attribute(
            socel,
            AttributionScope(
                FlowInstance("line-1", "electricity"),
                include_contained_operations=True,
            ),
        )

        self.assertEqual(default_result.unattributed, 12.0)
        self.assertEqual(result.for_event("event-1"), 12.0)
        self.assertEqual(result.unattributed, 0.0)

    def _configure_event(
        self,
        event_id: str,
        start: datetime,
        end: datetime | None,
    ) -> None:
        self.ocel.con.execute(
            """
            UPDATE events
            SET "ocel:timestamp" = ?,
                socel_class = 'op.manufacturing.forming',
                socel_end_time = ?
            WHERE "ocel:eid" = ?
            """,
            [start, end, event_id],
        )

    def _add_event(self, event_id: str, start: datetime, end: datetime) -> None:
        self.ocel.con.execute(
            """
            INSERT INTO events BY NAME
            SELECT
                ? AS "ocel:eid",
                'run' AS "ocel:activity",
                ? AS "ocel:timestamp",
                'op.manufacturing.forming' AS socel_class,
                ? AS socel_end_time
            """,
            [event_id, start, end],
        )
        self.ocel.con.execute(
            "INSERT INTO e2o VALUES (?, 'resource', 'machine-1')",
            [event_id],
        )

    def _add_interval(
        self,
        object_id: str,
        quantity: float,
        start: datetime,
        end: datetime,
    ) -> None:
        self.ocel.con.execute(
            "INSERT INTO socel_interval_records VALUES (?, ?, ?, ?, ?, ?)",
            ["record-1", "electricity", object_id, quantity, start, end],
        )


if __name__ == "__main__":
    unittest.main()
