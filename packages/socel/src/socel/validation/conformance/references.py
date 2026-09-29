import polars as pl
from ocelescope import OCEL

from socel._ocelescope import ident, reference_target
from socel.format.schema import EVENT_RECORDS, INTERVAL_RECORDS, TABLES
from socel.validation.check import Check, Finding, RowCheck, Subject, counted

# What a referenced table holds, for the messages.
_REFERENCED = {"socel_flow": "flow", "object": "object", "event": "event"}


class ReferencesExist(Check):
    """V2: every reference of the sOCEL tables points to an existing flow, object or event.

    Checked explicitly, as the thesis demands, rather than trusting SQLite to
    enforce foreign keys (it does not by default). The references are those the
    schema declares.
    """

    id = "V2"
    title = "Every flow, object and event a record references exists"
    requires = ("V1",)

    def run(self, subject: Subject) -> list[Finding]:
        ocel = subject.ocel
        findings: list[Finding] = []
        for table in TABLES:
            for key in table.foreign_keys:
                target_table, target_column = reference_target(
                    key.references_table, key.references_column
                )
                rows = ocel.sql(f"""
                    SELECT * FROM {ident(table.name)} t
                    WHERE t.{ident(key.column)} IS NOT NULL AND NOT EXISTS (
                        SELECT 1 FROM {ident(target_table)} r
                        WHERE r.{ident(target_column)} = t.{ident(key.column)}
                    )
                """).pl()
                if rows.height:
                    findings.append(
                        self.finding(
                            f"{counted(rows.height, 'row')} of {table.name} referencing "
                            f"{_REFERENCED[key.references_table]}s that do not exist "
                            f"({key.column}).",
                            rows,
                        )
                    )
        return findings


class RecordIdsDisjoint(RowCheck):
    """V3: no record id is used by both an interval record and an event-linked record."""

    id = "V3"
    title = "Interval and event-linked records do not share record ids"
    requires = ("V1",)

    def query(self, ocel: OCEL) -> str:
        return (
            f"SELECT record_id FROM {INTERVAL_RECORDS.name} "
            f"INTERSECT SELECT record_id FROM {EVENT_RECORDS.name}"
        )

    def describe(self, rows: pl.DataFrame) -> str:
        ids = counted(rows.height, "record id")
        return f"{ids} used by both interval and event-linked records."
