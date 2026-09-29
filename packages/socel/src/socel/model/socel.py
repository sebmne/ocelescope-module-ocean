from __future__ import annotations

import copy
from collections.abc import Sequence
from pathlib import Path

import duckdb
from ocelescope import OCEL
from ocelescope.ocel.filter import BaseFilter
from polars import LazyFrame

from socel._ocelescope import E2O, EID, OID, has_table, ident, is_read_only
from socel.format.attributes import events_sql, objects_sql
from socel.format.records import records_sql
from socel.format.schema import CONTAINED_IN, EVENT_RECORDS, FLOW, INTERVAL_RECORDS, TABLES
from socel.format.sqlite import read_tables, write_tables
from socel.format.tables import drop_dangling_references, require_table
from socel.validation import CONFORMANCE, Profile, SocelValidationError, ValidationReport


class SOCEL:
    """A sustainability-enriched object-centric event log (Heinisch 2026, Definition 5.3.2).

    An OCEL 2.0 log extended by the partition of its objects into handling units
    (HU) and the rest, of its events into operations (OP) and the rest, event end
    times, flows (FL), flow instances (FI), interval and event-linked records (IR,
    ER) and the containment of flow instances. Each is an accessor here, read
    lazily from the log's DuckDB database:

        socel = SOCEL.read("plant.sqlite")      # validated: V1–V9
        socel.handling_units                    # HU
        socel.operations                        # OP, with end_time
        socel.flows                             # FL, with unit, category, external_ref
        socel.flow_instances                    # FI
        socel.records                           # FR = IR ∪ ER, each with its span

    Read-only: an sOCEL is a value. `SOCELEditor` makes a changed one.
    """

    def __init__(self, ocel: OCEL) -> None:
        """Wraps an OCEL as it is, without validating it: for an OCEL known to be an
        sOCEL, or to validate one (`validate()`). `read` validates."""
        self._ocel = ocel

    @property
    def ocel(self) -> OCEL:
        """The underlying OCEL 2.0 log."""
        return self._ocel

    # ---- Reading, writing, validating ----------------------------------------

    @classmethod
    def read(cls, path: str | Path, *, validate: bool = True) -> SOCEL:
        """Reads an sOCEL from its SQLite serialization (Section 5.5).

        Raises:
            ValueError: Not a .sqlite file - the thesis defines no other serialization.
            SocelValidationError: The file is no conforming sOCEL (with `validate`).
        """
        path = Path(path)
        _require_sqlite(path)
        ocel = OCEL.read(path)
        read_tables(path, ocel)
        if validate:
            report = CONFORMANCE.run(ocel, file=path)
            if not report.is_conforming:
                ocel.close()
                raise SocelValidationError(report)
        return cls(ocel)

    def write(self, path: str | Path, *, validate: bool = True) -> None:
        """Writes the sOCEL as SQLite: the OCEL 2.0 base, then the sOCEL tables as
        the thesis declares them. An existing file is replaced.

        Raises:
            ValueError: Not a .sqlite path.
            SocelValidationError: The sOCEL does not conform (with `validate`).
            SocelWriteError: The data breaks a constraint the tables declare.
        """
        path = Path(path)
        _require_sqlite(path)
        if validate:
            report = self.validate()
            if not report.is_conforming:
                raise SocelValidationError(report)
        # Ocelescope writes through the log's own connection, which must be writable.
        source = copy.deepcopy(self._ocel) if is_read_only(self._ocel) else self._ocel
        try:
            path.unlink(missing_ok=True)
            source.write(path)
            write_tables(source, path)
        finally:
            if source is not self._ocel:
                source.close()

    def validate(self, profile: Profile = CONFORMANCE) -> ValidationReport:
        """Runs a profile's checks on the log, by default the conformance rules V1–V9."""
        return profile.run(self._ocel)

    @staticmethod
    def is_socel(ocel: OCEL) -> bool:
        """Whether the OCEL has the four sOCEL tables - not whether they conform."""
        return all(has_table(ocel, table.name) for table in TABLES)

    def filter(self, pipeline: Sequence[BaseFilter]) -> SOCEL:
        """The sOCEL filtered with Ocelescope's filters. Records and containments of
        objects and events filtered out go with them; flows stay."""
        filtered = self._ocel.filter(pipeline)
        drop_dangling_references(filtered)
        return SOCEL(filtered)

    def sql(self, query: str, params: list[object] | None = None) -> duckdb.DuckDBPyRelation:
        """A read query over the log's tables, the OCEL's and the sOCEL's."""
        return self._ocel.sql(query, params)

    # ---- Objects and events --------------------------------------------------

    @property
    def objects(self) -> LazyFrame:
        """O = HU ∪ Δ: object_id, object_type, socel_class, is_handling_unit."""
        return self.sql(objects_sql(self._ocel)).pl(lazy=True)

    @property
    def handling_units(self) -> LazyFrame:
        """HU: objects whose socel_class starts with `hu`."""
        return self.sql(f"SELECT * FROM ({objects_sql(self._ocel)}) WHERE is_handling_unit").pl(
            lazy=True
        )

    @property
    def events(self) -> LazyFrame:
        """E = OP ∪ Γ: event_id, activity, time, end_time, socel_class, is_operation."""
        return self.sql(events_sql(self._ocel)).pl(lazy=True)

    @property
    def operations(self) -> LazyFrame:
        """OP: events whose socel_class starts with `op`."""
        return self.sql(f"SELECT * FROM ({events_sql(self._ocel)}) WHERE is_operation").pl(
            lazy=True
        )

    @property
    def end_times(self) -> LazyFrame:
        """endtime, a partial function: event_id, end_time for the events that have one."""
        return self.sql(
            f"SELECT event_id, end_time FROM ({events_sql(self._ocel)}) WHERE end_time IS NOT NULL"
        ).pl(lazy=True)

    def operations_of(self, object_id: str) -> LazyFrame:
        """E_fi: the operations an object takes part in (Definition 6.0.1)."""
        return self.sql(
            f"""SELECT * FROM ({events_sql(self._ocel)}) WHERE is_operation AND event_id IN
                (SELECT {ident(EID)} FROM {E2O} WHERE {ident(OID)} = ?)""",
            [object_id],
        ).pl(lazy=True)

    # ---- Flows and records ---------------------------------------------------

    @property
    def flows(self) -> LazyFrame:
        """FL: flow_id, with the metadata unit, category and external_ref."""
        return self._table(FLOW.name)

    @property
    def interval_records(self) -> LazyFrame:
        """IR: record_id, flow_id, object_id, quantity, start_time, end_time."""
        return self._table(INTERVAL_RECORDS.name)

    @property
    def event_records(self) -> LazyFrame:
        """ER: record_id, flow_id, object_id, quantity, event_id."""
        return self._table(EVENT_RECORDS.name)

    @property
    def records(self) -> LazyFrame:
        """FR = IR ∪ ER, each with its span (Definition 6.1.1): record_id, kind
        ("interval" or "event"), flow_id, object_id, quantity, start_time, end_time,
        event_id. An event-linked record spans its event; end_time is null for a
        point event."""
        for table in (INTERVAL_RECORDS, EVENT_RECORDS):
            require_table(self._ocel, table)
        return self.sql(records_sql(self._ocel)).pl(lazy=True)

    @property
    def flow_instances(self) -> LazyFrame:
        """FI: object_id, flow_id - every pair in a record or a containment, as child
        or parent. A flow instance may exist without records (Section 5.4)."""
        for table in (INTERVAL_RECORDS, EVENT_RECORDS, CONTAINED_IN):
            require_table(self._ocel, table)
        return self.sql(f"""
            SELECT object_id, flow_id FROM {INTERVAL_RECORDS.name}
            UNION SELECT object_id, flow_id FROM {EVENT_RECORDS.name}
            UNION SELECT object_id, flow_id FROM {CONTAINED_IN.name}
            UNION SELECT parent_object_id, flow_id FROM {CONTAINED_IN.name}
        """).pl(lazy=True)

    @property
    def contained_in(self) -> LazyFrame:
        """containedin: flow_id, object_id, parent_object_id - the flow instance
        (object_id, flow_id) is contained in (parent_object_id, flow_id)."""
        return self._table(CONTAINED_IN.name)

    def _table(self, name: str) -> LazyFrame:
        require_table(self._ocel, next(table for table in TABLES if table.name == name))
        return self.sql(f"SELECT * FROM {ident(name)}").pl(lazy=True)

    def __repr__(self) -> str:
        return f"SOCEL({self._ocel!r})"


def _require_sqlite(path: Path) -> None:
    if path.suffix != ".sqlite":
        raise ValueError(f"An sOCEL is serialized as SQLite (.sqlite), not {path.suffix!r}.")
