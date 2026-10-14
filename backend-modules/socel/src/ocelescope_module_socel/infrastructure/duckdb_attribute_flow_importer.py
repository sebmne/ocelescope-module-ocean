from collections.abc import Mapping, Sequence

from ocelescope import OCEL
from ocelescope.ocel.constants.pm4py import ACTIVITY_COL, EID_COL, OID_COL, OTYPE_COL, TIMESTAMP_COL
from ocelescope.ocel.constants.tables import E2O_TABLE, EVENTS_TABLE, OBJECTS_TABLE
from socel.schema import EVENT_RECORDS, FLOW, SOCEL_CLASS, SOCEL_END_TIME

from ocelescope_module_socel.domain.exceptions import UnknownAttribute
from ocelescope_module_socel.domain.models.attribute_flows import AttributeFlow
from ocelescope_module_socel.domain.models.record_file import FlowDefinition

# The columns of the events table that are no attribute of the log's own.
_RESERVED = {EID_COL, ACTIVITY_COL, TIMESTAMP_COL, SOCEL_CLASS, SOCEL_END_TIME}
_NUMERIC = ("TINYINT", "SMALLINT", "INTEGER", "BIGINT", "HUGEINT", "FLOAT", "DOUBLE", "DECIMAL")


def _quoted(name: str) -> str:
    return '"' + name.replace('"', '""') + '"'


class DuckDbAttributeFlowImporter:
    """Writes the values of numeric event attributes as event-linked records,
    with SQL on the log's DuckDB database."""

    def write(
        self,
        ocel: OCEL,
        flows: Sequence[AttributeFlow],
        definitions: Mapping[str, FlowDefinition],
    ) -> None:
        con = ocel.con
        numeric = {
            name
            for name, declared, *_ in con.execute(f"DESCRIBE {EVENTS_TABLE}").fetchall()
            if name not in _RESERVED and declared.upper().startswith(_NUMERIC)
        }
        for flow in flows:
            if flow.attribute not in numeric:
                raise UnknownAttribute(flow.attribute)
        for flow in flows:
            definition = definitions[flow.flow_id]
            # The definition given replaces the log's flow of that name, as a
            # file's flows do; a file of the same build wrote the same one.
            con.execute(f"DELETE FROM {FLOW.name} WHERE flow_id = ?", [flow.flow_id])
            con.execute(
                f"INSERT INTO {FLOW.name} (flow_id, unit, category, external_ref) "
                "VALUES (?, ?, ?, ?)",
                [flow.flow_id, definition.unit, definition.category, definition.external_ref],
            )
            # One record per object of the type at the event; several objects
            # share the event's value equally.
            value = f"event.{_quoted(flow.attribute)}"
            signed = f"-abs({value})" if flow.direction == "out" else value
            con.execute(
                f"""
                INSERT INTO {EVENT_RECORDS.name} (record_id, flow_id, object_id, quantity, event_id)
                SELECT 'er-' || uuid()::VARCHAR, ?, involved."{OID_COL}",
                       {signed} / count(*) OVER (PARTITION BY involved."{EID_COL}"),
                       involved."{EID_COL}"
                FROM (
                    SELECT DISTINCT relation."{EID_COL}", relation."{OID_COL}"
                    FROM {E2O_TABLE} relation
                    JOIN {OBJECTS_TABLE} object USING ("{OID_COL}")
                    WHERE object."{OTYPE_COL}" = ?
                ) involved
                JOIN {EVENTS_TABLE} event USING ("{EID_COL}")
                WHERE {value} IS NOT NULL AND isfinite({value}::DOUBLE)
                """,
                [flow.flow_id, flow.object_type],
            )
