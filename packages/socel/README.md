# sOCEL

The sustainability-enriched OCEL (Heinisch 2026): an OCEL 2.0 log extended by
handling units and operations, event end times, flows, flow instances with their
interval and event-linked records, and the containment of flow instances
(Definition 5.3.2), serialized as four more SQLite tables and reserved attributes
(Section 5.5). Built on Ocelescope's `OCEL`; it depends on the `ocelescope`
library, not on the Ocelescope backend, its modules or OCEAn.

```python
from socel import SOCEL, SOCELEditor

socel = SOCEL.read("plant.sqlite")        # validated on import: V1–V9, the file's declarations included

socel.ocel                                # the underlying OCEL 2.0
socel.objects, socel.handling_units       # O, HU (socel_class starting with "hu")
socel.events, socel.operations            # E, OP (socel_class starting with "op"), with end_time
socel.end_times                           # endtime, for the events that have one
socel.flows                               # FL, with unit, category, external_ref
socel.flow_instances                      # FI, also those only established by containment
socel.interval_records, socel.event_records
socel.records                             # FR = IR ∪ ER, each with its span (§6.1)
socel.contained_in                        # containedin
socel.operations_of("furnace:1")          # E_fi (§6.0.1)

socel.write("plant.sqlite")               # validated on export, too

changed = (                               # an sOCEL is read-only; the editor makes a new one
    SOCELEditor(socel)                    # works on a copy, also of read-only OCELs
    .classify_object_type("Furnace", "pr.processing.thermal")
    .classify_activity("Heating", "op.manufacturing.thermal")
    .set_end_times({"e:heat:1": end})
    .add_flow("natural-gas", "m3", "energy.fuel")
    .add_interval_records(readings)       # polars DataFrames with the table's columns
    .build()                              # validated; SocelValidationError carries the report
)
```

## Structure

```
src/socel/
├── model/        Definition 5.3.2: SOCEL (read-only) and SOCELEditor
├── validation/   profiles: ordered pipelines of checks
│   ├── check.py        Check, RowCheck, Subject (the log, and the file it came from), Finding
│   ├── profile.py      Profile: runs checks in order, skips those whose requirements failed
│   ├── report.py       ValidationReport, SocelValidationError
│   └── conformance/    V1–V9, one class per rule (Appendix A.2)
├── format/       Section 5.5 and Appendix A.1: how an sOCEL is stored
│   ├── schema.py       the tables and reserved attributes, as data: the single source of truth
│   ├── attributes.py   socel_class and socel_end_time: reading and writing
│   ├── tables.py       creating, filling and pruning the four tables
│   ├── sqlite.py       the four tables in SQLite: read in UTC, written as declared
│   └── declared.py     what an SQLite file declares, for V1
├── taxonomy/     Chapter 4: one tree per kind of class, plus flow categories, as data
├── _ocelescope.py  the one module that knows Ocelescope's internal table and column names
└── errors.py     exceptions for misusing the library
```

Import-linter enforces the layers: model → validation → format → taxonomy and
the Ocelescope mapping → errors. The schema and the taxonomy import neither
Ocelescope, DuckDB nor polars.

## Design

- **The model is the definition.** `SOCEL` has one accessor per component of
  Definition 5.3.2, named as in the thesis; the tables are the serialization's
  business (`format/`).
- **Read-only, and an editor.** A formal sOCEL is a value. `SOCELEditor` changes a
  copy and hands over a new `SOCEL` with `build()`; afterwards it is closed.
- **Validated on every import, export and build**, as the thesis' own package does
  (Section 7.1.3). `validate=False` opens a log anyway, to look at what is wrong.
- **Composition, not inheritance.** `SOCEL` wraps an `OCEL`. Ocelescope's
  constructors, filters and copies build plain `OCEL`s, so a subclass would lose
  its type everywhere.
- **A rule is a class.** Its name says what must hold, its query selects the rows
  breaking it, and `requires` names the rules it builds on.

## Interpretations

Where the thesis leaves room, or Ocelescope differs from the OCEL 2.0 SQLite
format, the package decides as follows:

- **Classes are free text** (Section 5.5). An object is a handling unit iff its
  `socel_class` is non-null and its first segment is `hu`, an event an operation
  iff it is `op`, compared case-sensitively. Whether a class fits the taxonomy is a
  quality question, never a conformance error.
- **Initial values.** An object's `socel_class` is read from its row at
  1970-01-01 (Appendix A.1), which Ocelescope holds as a row of `object_changes`
  and writes back as the OCEL 2.0 initial row.
- **Timestamps** are UTC internally; offsets in a file are converted when read.
  They are written as the base log is (`2026-07-14T06:15:00+00:00`, a fraction
  only where there is one), so text and time order agree (Appendix A.2).
- **V1 on two sides.** The data as loaded (tables, columns, types, required values,
  unique keys), and for a file its declarations (types, NOT NULL, primary and
  foreign keys, CHECK constraints). Its CHECK conditions are also V4 and V9.
- **Ocelescope's extension tables.** Ocelescope reads every further table of an
  SQLite log (promi4s/ocelescope#458), but drops timestamp offsets and writes
  tables without declarations, empty ones not at all. The four sOCEL tables are
  therefore read again and written by this package.
- **Filtering** drops records and containments of filtered-out objects and events,
  and keeps the flows.

`pnpm run check:socel` (repository root) runs ruff, pyright (strict) and the
import-linter contracts in `pyproject.toml`; `pnpm run format` formats it.
