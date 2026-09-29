from ocelescope import OCEL

from socel._ocelescope import EID, EVENTS, column_type, has_table, ident
from socel.format.declared import declared_schema_problems
from socel.format.schema import DUCKDB_TYPES, SOCEL_END_TIME, TABLES, Table
from socel.validation.check import Check, Finding, Subject, counted


class TablesAndColumns(Check):
    """V1: the four tables exist with their columns, types, keys and constraints, and
    the reserved attributes have their types where present.

    Checked on two sides. The data as loaded: tables, columns, types, required
    values, unique primary keys. And, for an sOCEL read from a file, the file's
    declarations: declared types, NOT NULL, primary and foreign keys, CHECK
    constraints - a file can hold the right data in tables that declare none of
    them. The CHECK conditions themselves are rules of their own: start before
    end is V4, an object contained in itself a cycle for V9.
    """

    id = "V1"
    title = "The sOCEL tables exist with their columns, types, keys and constraints"

    def run(self, subject: Subject) -> list[Finding]:
        findings: list[Finding] = []
        if subject.file is not None:
            findings += [
                self.finding(f"In the file: {problem}")
                for problem in declared_schema_problems(subject.file)
            ]
        ocel = subject.ocel
        for table in TABLES:
            if not has_table(ocel, table.name):
                findings.append(self.finding(f"Table {table.name} is missing."))
                continue
            if self._columns(ocel, table, findings):
                self._required_values(ocel, table, findings)
                self._primary_key(ocel, table, findings)
        self._end_times(ocel, findings)
        return findings

    def _columns(self, ocel: OCEL, table: Table, findings: list[Finding]) -> bool:
        """Adds findings for missing or mistyped columns; whether all are fine."""
        ok = True
        for column in table.columns:
            actual = column_type(ocel, table.name, column.name)
            expected = DUCKDB_TYPES[column.type]
            if actual is None:
                findings.append(self.finding(f"{table.name}.{column.name} is missing."))
                ok = False
            elif actual != expected:
                findings.append(
                    self.finding(
                        f"{table.name}.{column.name} is {actual}, not {column.type} ({expected})."
                    )
                )
                ok = False
        return ok

    def _required_values(self, ocel: OCEL, table: Table, findings: list[Finding]) -> None:
        for name in table.required_columns:
            rows = ocel.sql(f"SELECT * FROM {ident(table.name)} WHERE {ident(name)} IS NULL").pl()
            if rows.height:
                findings.append(
                    self.finding(
                        f"{counted(rows.height, 'row')} of {table.name} without {name} "
                        "(missing, or not readable as its type).",
                        rows,
                    )
                )

    def _primary_key(self, ocel: OCEL, table: Table, findings: list[Finding]) -> None:
        key = ", ".join(ident(name) for name in table.primary_key)
        rows = ocel.sql(
            f"SELECT {key}, count(*) AS rows FROM {ident(table.name)} "
            f"GROUP BY {key} HAVING count(*) > 1"
        ).pl()
        if rows.height:
            findings.append(
                self.finding(
                    f"{counted(rows.height, 'value')} of the primary key "
                    f"({', '.join(table.primary_key)}) of {table.name} occurring more than once.",
                    rows,
                )
            )

    def _end_times(self, ocel: OCEL, findings: list[Finding]) -> None:
        """The reserved attribute socel_end_time, where present, holds timestamps."""
        if column_type(ocel, EVENTS, SOCEL_END_TIME) is None:
            return
        rows = ocel.sql(
            f"SELECT {ident(EID)} AS event_id, {SOCEL_END_TIME} FROM {EVENTS} "
            f"WHERE {SOCEL_END_TIME} IS NOT NULL "
            f"AND TRY_CAST({SOCEL_END_TIME} AS TIMESTAMP) IS NULL"
        ).pl()
        if rows.height:
            findings.append(
                self.finding(
                    f"{counted(rows.height, 'event')} with a socel_end_time that is no timestamp.",
                    rows,
                )
            )
