from __future__ import annotations

import unittest
from datetime import UTC, datetime, timedelta

import polars as pl
from ocelescope import OCEL, OCELExtension
from ocelescope.ocel.constants.pm4py import (
    ACTIVITY_COL,
    E2O_QUALIFIER,
    EID_COL,
    OID_COL,
    OTYPE_COL,
    TIMESTAMP_COL,
)

from socel import DEFAULT_TAXONOMY, SOCEL, SOCELValidationError


def make_ocel() -> OCEL:
    return OCEL.from_frames(
        events=pl.DataFrame(
            {
                EID_COL: ["event-1"],
                ACTIVITY_COL: ["run"],
                TIMESTAMP_COL: [datetime(2026, 1, 1, 10, tzinfo=UTC)],
            }
        ),
        objects=pl.DataFrame({OID_COL: ["machine-1"], OTYPE_COL: ["machine"]}),
        relations=pl.DataFrame(
            {
                EID_COL: ["event-1"],
                E2O_QUALIFIER: ["resource"],
                OID_COL: ["machine-1"],
            }
        ),
    )


def add_extension_tables(ocel: OCEL) -> None:
    ocel.con.execute("""
        CREATE TABLE socel_flow (
            flow_id VARCHAR,
            unit VARCHAR,
            category VARCHAR,
            external_ref VARCHAR
        );
        CREATE TABLE socel_interval_records (
            record_id VARCHAR,
            flow_id VARCHAR,
            object_id VARCHAR,
            quantity DOUBLE,
            start_time TIMESTAMP,
            end_time TIMESTAMP
        );
        CREATE TABLE socel_event_records (
            record_id VARCHAR,
            flow_id VARCHAR,
            object_id VARCHAR,
            quantity DOUBLE,
            event_id VARCHAR
        );
        CREATE TABLE socel_containedin (
            flow_id VARCHAR,
            object_id VARCHAR,
            parent_object_id VARCHAR
        );
    """)


class ValidationPipelineTests(unittest.TestCase):
    def test_socel_implements_ocelescope_extension_contract(self) -> None:
        self.assertTrue(issubclass(SOCEL, OCELExtension))
        self.assertEqual(SOCEL.id, "socel")
        self.assertEqual(SOCEL.label, "sOCEL")

    def test_valid_extension_becomes_socel(self) -> None:
        ocel = make_ocel()
        try:
            add_extension_tables(ocel)
            socel = SOCEL.from_ocel(ocel)
            self.assertIs(socel.ocel, ocel)
            self.assertIs(socel.taxonomies, DEFAULT_TAXONOMY)
            self.assertTrue(SOCEL.is_valid(ocel))
        finally:
            ocel.close()

    def test_missing_structure_only_produces_v1_messages(self) -> None:
        ocel = make_ocel()
        try:
            with self.assertRaises(SOCELValidationError) as raised:
                SOCEL.from_ocel(ocel)

            self.assertEqual(len(raised.exception.messages), 4)
            self.assertTrue(
                all(message.startswith("[V1]") for message in raised.exception.messages)
            )
            self.assertFalse(SOCEL.is_valid(ocel))
        finally:
            ocel.close()

    def test_independent_rules_are_aggregated(self) -> None:
        ocel = make_ocel()
        try:
            add_extension_tables(ocel)
            ocel.con.execute(
                "INSERT INTO socel_flow VALUES ('electricity', 'kWh', 'energy', NULL)"
            )
            start = datetime(2026, 1, 1, 10, tzinfo=UTC)
            ocel.con.executemany(
                "INSERT INTO socel_interval_records VALUES (?, ?, ?, ?, ?, ?)",
                [
                    (
                        "r1",
                        "electricity",
                        "machine-1",
                        2.0,
                        start,
                        start + timedelta(minutes=20),
                    ),
                    (
                        "r2",
                        "electricity",
                        "machine-1",
                        3.0,
                        start + timedelta(minutes=10),
                        start + timedelta(minutes=30),
                    ),
                    ("r3", "electricity", "machine-1", 1.0, start, start),
                ],
            )
            ocel.con.execute(
                "INSERT INTO socel_event_records VALUES "
                "('r1', 'electricity', 'machine-1', 1.0, 'event-1')"
            )

            with self.assertRaises(SOCELValidationError) as raised:
                SOCEL.from_ocel(ocel)

            codes = {message[:4] for message in raised.exception.messages}
            self.assertEqual(codes, {"[V3]", "[V4]"})
        finally:
            ocel.close()

    def test_taxonomy_violations_are_aggregated_by_v10(self) -> None:
        ocel = make_ocel()
        try:
            add_extension_tables(ocel)
            ocel.con.executemany(
                "INSERT INTO socel_flow VALUES (?, ?, ?, NULL)",
                [
                    ("missing", "kg", None),
                    ("custom", "kg", "company.custom"),
                ],
            )
            ocel.con.execute("ALTER TABLE events ADD COLUMN socel_class VARCHAR")
            ocel.con.execute("UPDATE events SET socel_class = 'op.custom'")
            ocel.con.execute(
                "ALTER TABLE object_changes ADD COLUMN socel_class VARCHAR"
            )
            ocel.con.execute(
                """
                INSERT INTO object_changes BY NAME
                SELECT
                    'machine-1' AS "ocel:oid",
                    TIMESTAMP '1970-01-01' AS "ocel:timestamp",
                    'socel_class' AS "ocel:field",
                    'pr.custom' AS socel_class
                """
            )

            with self.assertRaises(SOCELValidationError) as raised:
                SOCEL.from_ocel(ocel)

            self.assertEqual(len(raised.exception.messages), 4)
            self.assertTrue(
                all(
                    message.startswith("[V10]") for message in raised.exception.messages
                )
            )
        finally:
            ocel.close()


if __name__ == "__main__":
    unittest.main()
