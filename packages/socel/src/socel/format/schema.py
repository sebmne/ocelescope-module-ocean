"""The sOCEL serialization as the thesis defines it: four tables and reserved attributes.

The single source of truth for the format. The DuckDB tables, the SQLite DDL,
the structural check (V1, on the data and on the file), the reference check
(V2), reading, writing and filtering are all derived from these specs.

Source: Heinisch (2026), Section 5.5 and Appendix A.1.
"""

from dataclasses import dataclass
from typing import Literal

SqlType = Literal["TEXT", "REAL", "TIMESTAMP"]

# How each declared SQLite type is held in DuckDB.
DUCKDB_TYPES: dict[SqlType, str] = {"TEXT": "VARCHAR", "REAL": "DOUBLE", "TIMESTAMP": "TIMESTAMP"}


@dataclass(frozen=True)
class Column:
    name: str
    type: SqlType
    nullable: bool = False


@dataclass(frozen=True)
class ForeignKey:
    """`column` references `references_table(references_column)`.

    Named as in the SQLite serialization: `object` and `event` are the OCEL 2.0
    base tables, whose ids are `ocel_id`.
    """

    column: str
    references_table: str
    references_column: str


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[Column, ...]
    primary_key: tuple[str, ...]
    foreign_keys: tuple[ForeignKey, ...] = ()
    # SQL conditions every row must satisfy, as declared in the DDL.
    checks: tuple[str, ...] = ()

    @property
    def column_names(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns)

    @property
    def required_columns(self) -> tuple[str, ...]:
        return tuple(column.name for column in self.columns if not column.nullable)

    def sqlite_ddl(self) -> str:
        """The CREATE TABLE statement exactly as the thesis declares it."""
        lines = [
            f"{column.name} {column.type}{'' if column.nullable else ' NOT NULL'}"
            for column in self.columns
        ]
        lines.append(f"PRIMARY KEY ({', '.join(self.primary_key)})")
        lines.extend(f"CHECK ({check})" for check in self.checks)
        lines.extend(
            f"FOREIGN KEY ({key.column}) REFERENCES {key.references_table}({key.references_column})"
            for key in self.foreign_keys
        )
        body = ",\n    ".join(lines)
        return f"CREATE TABLE {self.name} (\n    {body}\n)"

    def duckdb_ddl(self) -> str:
        """The table as held in DuckDB: typed columns, no constraints.

        Constraints are deliberately left out: an sOCEL that breaks them must
        still load, so that validation can say where. Writing to SQLite, where
        the declared constraints apply, is where they are enforced.
        """
        columns = ", ".join(f"{column.name} {DUCKDB_TYPES[column.type]}" for column in self.columns)
        return f"CREATE TABLE {self.name} ({columns})"


_FLOW = ForeignKey("flow_id", "socel_flow", "flow_id")
_OBJECT = ForeignKey("object_id", "object", "ocel_id")

FLOW = Table(
    name="socel_flow",
    columns=(
        Column("flow_id", "TEXT"),
        Column("unit", "TEXT"),
        Column("category", "TEXT", nullable=True),
        Column("external_ref", "TEXT", nullable=True),
    ),
    primary_key=("flow_id",),
)

INTERVAL_RECORDS = Table(
    name="socel_interval_records",
    columns=(
        Column("record_id", "TEXT"),
        Column("flow_id", "TEXT"),
        Column("object_id", "TEXT"),
        Column("quantity", "REAL"),
        Column("start_time", "TIMESTAMP"),
        Column("end_time", "TIMESTAMP"),
    ),
    primary_key=("record_id",),
    foreign_keys=(_FLOW, _OBJECT),
    checks=("start_time < end_time",),
)

EVENT_RECORDS = Table(
    name="socel_event_records",
    columns=(
        Column("record_id", "TEXT"),
        Column("flow_id", "TEXT"),
        Column("object_id", "TEXT"),
        Column("quantity", "REAL"),
        Column("event_id", "TEXT"),
    ),
    primary_key=("record_id",),
    foreign_keys=(_FLOW, _OBJECT, ForeignKey("event_id", "event", "ocel_id")),
)

CONTAINED_IN = Table(
    name="socel_containedin",
    columns=(
        Column("flow_id", "TEXT"),
        Column("object_id", "TEXT"),
        Column("parent_object_id", "TEXT"),
    ),
    primary_key=("flow_id", "object_id"),
    foreign_keys=(_FLOW, _OBJECT, ForeignKey("parent_object_id", "object", "ocel_id")),
    checks=("object_id <> parent_object_id",),
)

# In dependency order: flows before the tables that reference them.
TABLES: tuple[Table, ...] = (FLOW, INTERVAL_RECORDS, EVENT_RECORDS, CONTAINED_IN)


@dataclass(frozen=True)
class ReservedAttribute:
    """An ordinary OCEL attribute whose name the sOCEL reserves. Optional."""

    name: str
    entity: Literal["object", "event"]
    type: Literal["TEXT", "TIMESTAMP"]
    meaning: str


SOCEL_CLASS = "socel_class"
SOCEL_END_TIME = "socel_end_time"

# The first segment of socel_class that puts an object into HU (handling units)
# or an event into OP (operations); compared case-sensitively (Section 5.5).
HANDLING_UNIT = "hu"
OPERATION = "op"

RESERVED_ATTRIBUTES: tuple[ReservedAttribute, ...] = (
    ReservedAttribute(
        SOCEL_CLASS,
        "object",
        "TEXT",
        "Classifies objects, especially handling units and process resources. "
        "Read from the object's initial value; later changes are ignored.",
    ),
    ReservedAttribute(SOCEL_CLASS, "event", "TEXT", "Classifies operation events."),
    ReservedAttribute(SOCEL_END_TIME, "event", "TIMESTAMP", "Observed end time of an event."),
)
