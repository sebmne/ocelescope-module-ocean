import unittest
from datetime import UTC, datetime, timedelta

from test_validation import add_extension_tables, make_ocel

from socel import SOCEL, FlowInstance, IntervalRecord
from socel.analysis import AnalysisWindow, quantity, share


def timestamp(hour: int, minute: int = 0) -> datetime:
    """Match the timezone-naive timestamps returned by DuckDB ``TIMESTAMP``."""
    return datetime(2026, 1, 1, hour, minute, tzinfo=UTC).replace(tzinfo=None)


class AnalysisWindowTests(unittest.TestCase):
    def test_window_requires_increasing_timestamps(self) -> None:
        start = timestamp(10)

        with self.assertRaisesRegex(ValueError, "start before it ends"):
            AnalysisWindow(start, start)
        with self.assertRaisesRegex(ValueError, "start before it ends"):
            AnalysisWindow(start, start - timedelta(minutes=1))

    def test_window_requires_compatible_time_zones(self) -> None:
        with self.assertRaisesRegex(ValueError, "compatible time zones"):
            AnalysisWindow(
                timestamp(10),
                datetime(2026, 1, 1, 11, tzinfo=UTC),
            )


class QuantificationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.ocel = make_ocel()
        add_extension_tables(self.ocel)

    def tearDown(self) -> None:
        self.ocel.close()

    def test_interval_share_is_proportional_to_overlap(self) -> None:
        socel = SOCEL.from_ocel(self.ocel)
        start = timestamp(10)
        record = IntervalRecord(
            id="record-1",
            instance=FlowInstance("machine-1", "electricity"),
            quantity=12.0,
            start=start,
            end=start + timedelta(hours=1),
        )

        result = share(
            socel,
            record,
            AnalysisWindow(
                start + timedelta(minutes=15),
                start + timedelta(minutes=45),
            ),
        )

        self.assertEqual(result, 6.0)

    def test_duration_event_share_is_proportional_to_overlap(self) -> None:
        self._add_flow_and_event_record(quantity=12.0)
        self.ocel.con.execute("ALTER TABLE events ADD COLUMN socel_end_time TIMESTAMP")
        self.ocel.con.execute(
            "UPDATE events SET socel_end_time = TIMESTAMP '2026-01-01 11:00:00'"
        )
        socel = SOCEL.from_ocel(self.ocel)
        record = socel.measurements.for_event("event-1")[0]

        result = share(
            socel,
            record,
            AnalysisWindow(
                timestamp(10, 15),
                timestamp(10, 45),
            ),
        )

        self.assertEqual(result, 6.0)

    def test_point_event_uses_half_open_window(self) -> None:
        self._add_flow_and_event_record(quantity=3.0)
        socel = SOCEL.from_ocel(self.ocel)
        record = socel.measurements.for_event("event-1")[0]

        before = AnalysisWindow(
            timestamp(9),
            timestamp(10),
        )
        after = AnalysisWindow(
            timestamp(10),
            timestamp(11),
        )

        self.assertEqual(share(socel, record, before), 0.0)
        self.assertEqual(share(socel, record, after), 3.0)

    def test_quantity_sums_all_record_shares_of_an_instance(self) -> None:
        self.ocel.con.execute(
            "INSERT INTO socel_flow VALUES "
            "('electricity', 'kWh', 'energy.electricity', NULL)"
        )
        self.ocel.con.execute(
            "UPDATE events SET \"ocel:timestamp\" = TIMESTAMP '2026-01-01 12:00:00'"
        )
        self.ocel.con.executemany(
            "INSERT INTO socel_interval_records VALUES (?, ?, ?, ?, ?, ?)",
            [
                (
                    "interval-1",
                    "electricity",
                    "machine-1",
                    10.0,
                    timestamp(10),
                    timestamp(11),
                ),
                (
                    "interval-2",
                    "electricity",
                    "machine-1",
                    20.0,
                    timestamp(11),
                    timestamp(12),
                ),
            ],
        )
        self.ocel.con.execute(
            "INSERT INTO socel_event_records VALUES "
            "('event-record', 'electricity', 'machine-1', 5.0, 'event-1')"
        )
        socel = SOCEL.from_ocel(self.ocel)

        result = quantity(
            socel,
            FlowInstance("machine-1", "electricity"),
            AnalysisWindow(
                timestamp(10, 30),
                timestamp(12, 1),
            ),
        )

        self.assertEqual(result, 30.0)

    def _add_flow_and_event_record(self, quantity: float) -> None:
        self.ocel.con.execute(
            "INSERT INTO socel_flow VALUES "
            "('electricity', 'kWh', 'energy.electricity', NULL)"
        )
        self.ocel.con.execute(
            "INSERT INTO socel_event_records VALUES (?, ?, ?, ?, ?)",
            ["event-record", "electricity", "machine-1", quantity, "event-1"],
        )


if __name__ == "__main__":
    unittest.main()
