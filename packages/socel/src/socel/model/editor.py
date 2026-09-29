from __future__ import annotations

import copy
from collections.abc import Mapping
from datetime import datetime
from typing import Self

import polars as pl
from ocelescope import OCEL

from socel._ocelescope import ACTIVITY, EID, EVENTS, OBJECT_TYPE, OBJECTS, OID, ident
from socel.errors import EditorClosedError
from socel.format.attributes import write_event_values, write_object_classes
from socel.format.schema import (
    CONTAINED_IN,
    EVENT_RECORDS,
    FLOW,
    INTERVAL_RECORDS,
    SOCEL_CLASS,
    SOCEL_END_TIME,
)
from socel.format.tables import append_rows, create_missing_tables
from socel.model.socel import SOCEL
from socel.validation import SocelValidationError


class SOCELEditor:
    """Makes an sOCEL: from an OCEL, or from an sOCEL to change.

    Works on a copy - the source stays as it is, so a read-only OCEL (as the
    Ocelescope backend hands out) is fine - and hands over the result with
    `build()`, validated:

        socel = (
            SOCELEditor(ocel)
            .classify_object_type("Furnace", "pr.processing.thermal")
            .classify_activity("Heating", "op.manufacturing.thermal")
            .add_flow("natural-gas", "m3", "energy.fuel")
            .add_interval_records(readings)
            .build()
        )

    Classes are free text (Section 5.5): an object is a handling unit iff its class
    starts with `hu`, an event an operation iff it starts with `op`; the rest of a
    class is unrestricted, and None leaves an entity unclassified. Whether classes
    fit the taxonomy is a quality question, not one the editor decides.
    """

    def __init__(self, source: OCEL | SOCEL) -> None:
        ocel = source.ocel if isinstance(source, SOCEL) else source
        self._ocel: OCEL = copy.deepcopy(ocel)
        create_missing_tables(self._ocel)
        self._closed = False

    # ---- Classes and end times (the reserved attributes) ---------------------

    def classify_objects(self, classes: Mapping[str, str | None]) -> Self:
        """Sets objects' socel_class: object id -> class (None: unclassified).

        Raises:
            ValueError: Unknown object ids.
        """
        frame = pl.DataFrame(
            {"object_id": list(classes), "socel_class": list(classes.values())},
            schema={"object_id": pl.String, "socel_class": pl.String},
        )
        self._require_known(frame["object_id"], OBJECTS, OID, "objects")
        write_object_classes(self._open(), frame)
        return self

    def classify_object_type(self, object_type: str, socel_class: str | None) -> Self:
        """Gives every object of a type the class.

        Raises:
            ValueError: The log has no objects of the type.
        """
        ids = self._ids(OBJECTS, OID, OBJECT_TYPE, object_type, "objects of type")
        return self.classify_objects(dict.fromkeys(ids, socel_class))

    def classify_events(self, classes: Mapping[str, str | None]) -> Self:
        """Sets events' socel_class: event id -> class (None: unclassified).

        Raises:
            ValueError: Unknown event ids.
        """
        frame = pl.DataFrame(
            {"event_id": list(classes), "value": list(classes.values())},
            schema={"event_id": pl.String, "value": pl.String},
        )
        self._require_known(frame["event_id"], EVENTS, EID, "events")
        write_event_values(self._open(), SOCEL_CLASS, "VARCHAR", frame)
        return self

    def classify_activity(self, activity: str, socel_class: str | None) -> Self:
        """Gives every event of an activity the class.

        Raises:
            ValueError: The log has no events of the activity.
        """
        ids = self._ids(EVENTS, EID, ACTIVITY, activity, "events of activity")
        return self.classify_events(dict.fromkeys(ids, socel_class))

    def set_end_times(self, end_times: Mapping[str, datetime | None]) -> Self:
        """Sets events' observed end time, in UTC: event id -> end (None: a point event).

        Raises:
            ValueError: Unknown event ids.
        """
        frame = pl.DataFrame(
            {"event_id": list(end_times), "value": list(end_times.values())},
            schema={"event_id": pl.String, "value": pl.Datetime("us")},
        )
        self._require_known(frame["event_id"], EVENTS, EID, "events")
        write_event_values(self._open(), SOCEL_END_TIME, "TIMESTAMP", frame)
        return self

    # ---- Flows, records, containment -----------------------------------------

    def add_flow(
        self,
        flow_id: str,
        unit: str,
        category: str | None = None,
        external_ref: str | None = None,
    ) -> Self:
        """Adds one flow. `category` is meant to be a flow category of the taxonomy,
        e.g. `energy.fuel`, but any string is admissible (Section 5.5)."""
        return self.add_flows(
            pl.DataFrame(
                [
                    {
                        "flow_id": flow_id,
                        "unit": unit,
                        "category": category,
                        "external_ref": external_ref,
                    }
                ],
                schema={name: pl.String for name in FLOW.column_names},
            )
        )

    def add_flows(self, rows: pl.DataFrame) -> Self:
        """Adds flows: flow_id, unit, and optionally category, external_ref."""
        append_rows(self._open(), FLOW, rows)
        return self

    def add_interval_records(self, rows: pl.DataFrame) -> Self:
        """Adds interval records: record_id, flow_id, object_id, quantity (signed:
        positive flows into the object), start_time, end_time (UTC)."""
        append_rows(self._open(), INTERVAL_RECORDS, rows)
        return self

    def add_event_records(self, rows: pl.DataFrame) -> Self:
        """Adds event-linked records: record_id, flow_id, object_id, quantity, event_id.
        The object need not take part in the event (Section 5.3)."""
        append_rows(self._open(), EVENT_RECORDS, rows)
        return self

    def add_containment(self, rows: pl.DataFrame) -> Self:
        """Adds containment: flow_id, object_id, parent_object_id - the flow instance
        (object_id, flow_id) reports within (parent_object_id, flow_id)."""
        append_rows(self._open(), CONTAINED_IN, rows)
        return self

    # ---- Finishing -----------------------------------------------------------

    def build(self, *, validate: bool = True) -> SOCEL:
        """The sOCEL as edited. The editor is done afterwards; a new one changes it.

        Raises:
            SocelValidationError: The result does not conform (with `validate`); the
                editor stays open, so the problem can be fixed.
        """
        socel = SOCEL(self._open())
        if validate:
            report = socel.validate()
            if not report.is_conforming:
                raise SocelValidationError(report)
        self._closed = True
        return socel

    # ---- Internals -----------------------------------------------------------

    def _open(self) -> OCEL:
        if self._closed:
            raise EditorClosedError("This editor has built its sOCEL; start a new one.")
        return self._ocel

    def _ids(self, table: str, id_column: str, column: str, value: str, what: str) -> list[str]:
        ids = (
            self._open()
            .sql(f"SELECT {ident(id_column)} FROM {table} WHERE {ident(column)} = ?", [value])
            .pl()[id_column]
            .to_list()
        )
        if not ids:
            raise ValueError(f"The log has no {what} {value!r}.")
        return [str(i) for i in ids]

    def _require_known(self, ids: pl.Series, table: str, id_column: str, what: str) -> None:
        con = self._open().con
        con.register("_socel_ids", ids.to_frame("id"))
        try:
            unknown = [
                str(value)
                for (value,) in con.execute(
                    f"SELECT id FROM _socel_ids EXCEPT SELECT {ident(id_column)} FROM {table}"
                ).fetchall()
            ]
        finally:
            con.unregister("_socel_ids")
        if unknown:
            shown = ", ".join(sorted(unknown)[:5])
            raise ValueError(f"Unknown {what}: {shown}{' ...' if len(unknown) > 5 else ''}")
