"""The sOCEL extension schema used by validation and future table access."""

from dataclasses import dataclass
from typing import Literal

LogicalType = Literal["text", "real", "timestamp"]


@dataclass(frozen=True)
class Column:
    name: str
    type: LogicalType
    nullable: bool = False


@dataclass(frozen=True)
class Table:
    name: str
    columns: tuple[Column, ...]
    key: tuple[str, ...]


FLOW = Table(
    name="socel_flow",
    columns=(
        Column("flow_id", "text"),
        Column("unit", "text"),
        Column("category", "text", nullable=True),
        Column("external_ref", "text", nullable=True),
    ),
    key=("flow_id",),
)

INTERVAL_RECORDS = Table(
    name="socel_interval_records",
    columns=(
        Column("record_id", "text"),
        Column("flow_id", "text"),
        Column("object_id", "text"),
        Column("quantity", "real"),
        Column("start_time", "timestamp"),
        Column("end_time", "timestamp"),
    ),
    key=("record_id",),
)

EVENT_RECORDS = Table(
    name="socel_event_records",
    columns=(
        Column("record_id", "text"),
        Column("flow_id", "text"),
        Column("object_id", "text"),
        Column("quantity", "real"),
        Column("event_id", "text"),
    ),
    key=("record_id",),
)

CONTAINED_IN = Table(
    name="socel_containedin",
    columns=(
        Column("flow_id", "text"),
        Column("object_id", "text"),
        Column("parent_object_id", "text"),
    ),
    key=("flow_id", "object_id"),
)

TABLES = (FLOW, INTERVAL_RECORDS, EVENT_RECORDS, CONTAINED_IN)

SOCEL_CLASS = "socel_class"
SOCEL_END_TIME = "socel_end_time"


def has_logical_type(database_type: str, expected: LogicalType) -> bool:
    """Whether a DuckDB type represents the expected sOCEL logical type."""
    actual = database_type.upper()
    if expected == "text":
        return actual == "VARCHAR"
    if expected == "real":
        return actual in {"DOUBLE", "FLOAT", "REAL"} or actual.startswith("DECIMAL")
    return actual.startswith("TIMESTAMP")
