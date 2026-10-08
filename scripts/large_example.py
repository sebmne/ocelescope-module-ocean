"""Generates a large example to try the module at a realistic size.

A synthetic plant with 200,000 events and 700,000 objects (600,000 workpieces,
90,000 orders, 2,000 machines in 100 lines in 10 halls in one plant), and a month
of meter readings for it. Written to `data/`:

- `event_logs/large_plant.db`: the plain log, to try the builder on;
- `flow_records/large_plant_records.csv`: its record file, 1.8 million rows;
- `event_logs/large_plant_socel.db`: the sOCEL built from both, with the meters
  nested (machine in line in hall in plant), to try the overview on.

Run from the repository root:

    uv run python scripts/large_example.py            # generate the files
    uv run python scripts/large_example.py --register # and list them as examples

The files are large and not meant for git (see `.gitignore`). `--register` adds
them to `data/event_logs.json`; restart the backend to see them.
"""

import json
import sys
import time
from pathlib import Path

import duckdb
from ocelescope import OCEL
from ocelescope_module_socel.application.use_cases.build_socel import (
    BuildSocel,
    BuildSocelCommand,
    RecordsToImport,
)
from ocelescope_module_socel.domain.models.record_file import FlowDefinition
from ocelescope_module_socel.infrastructure.duckdb_log_classifier import DuckDbLogClassifier
from ocelescope_module_socel.infrastructure.duckdb_record_importer import DuckDbRecordImporter
from socel import SOCEL

DATA = Path(__file__).resolve().parent.parent / "data"
LOG = DATA / "event_logs" / "large_plant.db"
SOCEL_LOG = DATA / "event_logs" / "large_plant_socel.db"
RECORDS = DATA / "flow_records" / "large_plant_records.csv"

ACTIVITIES = {
    "release order": None,
    "cut blank": "op.manufacturing.separating",
    "stamp": "op.manufacturing.forming",
    "deburr": "op.manufacturing.separating",
    "weld": "op.manufacturing.joining",
    "inspect weld": None,
    "paint": "op.manufacturing.surface.coating",
    "cure": "op.manufacturing.thermal",
    "assemble": "op.manufacturing.joining",
    "test": None,
    "pack": "op.logistics.packaging",
    "ship": "op.logistics.transport",
}
OBJECT_TYPES = {
    "workpiece": "hu",
    "machine": "pr.processing.mechanical",
    "line": "pr.processing",
    "hall": "pr.infrastructure",
    "plant": "pr.infrastructure",
}
FLOWS = {
    "electricity": FlowDefinition(unit="kWh", category="energy.electricity"),
    "natural_gas": FlowDefinition(unit="kWh", category="energy.fuel"),
    "steel_sheet": FlowDefinition(unit="kg", category="material.workpiece"),
    "steel_scrap": FlowDefinition(unit="kg", category="material.workpiece"),
    "paint": FlowDefinition(unit="kg", category="material.auxiliary"),
}


def generate_log_and_records() -> None:
    for path in (LOG, RECORDS):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.unlink(missing_ok=True)
    con = duckdb.connect(str(LOG))
    con.execute("SET TimeZone = 'UTC'")
    con.execute("""
        CREATE TABLE objects AS
        SELECT 'PLANT' AS "ocel:oid", 'plant' AS "ocel:type"
        UNION ALL SELECT format('H{:02d}', i), 'hall' FROM range(1, 11) t(i)
        UNION ALL SELECT format('L{:03d}', i), 'line' FROM range(1, 101) t(i)
        UNION ALL SELECT format('M{:04d}', i), 'machine' FROM range(1, 2001) t(i)
        UNION ALL SELECT format('O{:06d}', i), 'order' FROM range(1, 90001) t(i)
        UNION ALL SELECT format('W{:07d}', i), 'workpiece' FROM range(1, 600001) t(i)
        UNION ALL SELECT format('LOT{:05d}', i), 'material_lot' FROM range(1, 7890) t(i)
    """)
    activities = ", ".join(f"({i}, '{name}')" for i, name in enumerate(ACTIVITIES))
    con.execute(f"CREATE TEMP TABLE activity AS SELECT * FROM (VALUES {activities}) v(n, name)")
    con.execute("""
        CREATE TEMP TABLE happened AS
        SELECT i, format('E{:06d}', i) AS eid, i % 12 AS activity,
               TIMESTAMP '2026-03-01 00:00:00' + to_seconds(i * 13) AS happened_at,
               (i * 3) % 600000 + 1 AS workpiece, hash(i) % 2000 + 1 AS machine
        FROM range(0, 200000) t(i)
    """)
    con.execute("""
        CREATE TABLE events AS
        SELECT eid AS "ocel:eid", activity.name AS "ocel:activity", happened_at AS "ocel:timestamp",
               CASE WHEN happened.activity = 9
                    THEN (CASE WHEN i % 50 = 0 THEN 'fail' ELSE 'pass' END) END AS result
        FROM happened JOIN activity ON activity.n = happened.activity ORDER BY i
    """)
    con.execute("""
        CREATE TABLE e2o AS
        SELECT eid AS "ocel:eid", 'workpiece' AS "ocel:qualifier",
               format('W{:07d}', workpiece) AS "ocel:oid" FROM happened
        UNION ALL SELECT eid, 'machine', format('M{:04d}', machine) FROM happened
        UNION ALL SELECT eid, 'order', format('O{:06d}', (workpiece - 1) * 90000 // 600000 + 1)
        FROM happened
    """)
    con.execute("""
        CREATE TABLE o2o AS
        SELECT format('M{:04d}', i) AS "ocel:oid_1", 'part_of' AS "ocel:qualifier",
               format('L{:03d}', (i - 1) // 20 + 1) AS "ocel:oid_2" FROM range(1, 2001) t(i)
        UNION ALL SELECT format('L{:03d}', i), 'part_of', format('H{:02d}', (i - 1) // 10 + 1)
        FROM range(1, 101) t(i)
        UNION ALL SELECT format('H{:02d}', i), 'part_of', 'PLANT' FROM range(1, 11) t(i)
        UNION ALL SELECT format('W{:07d}', i), 'belongs_to',
               format('O{:06d}', (i - 1) * 90000 // 600000 + 1) FROM range(1, 600001) t(i)
    """)
    con.execute("""
        CREATE TABLE object_changes AS
        SELECT format('M{:04d}', i) AS "ocel:oid", TIMESTAMP '1970-01-01 00:00:00' AS "ocel:timestamp",
               'meter_id' AS "ocel:field", format('Z-{:05d}', 40000 + i) AS meter_id
        FROM range(1, 2001) t(i)
    """)
    con.execute(
        'CREATE TABLE quantities ("ocel:oid" VARCHAR, "qel:item_type" VARCHAR, '
        '"qel:quantity" DOUBLE)'
    )
    con.execute('CREATE TABLE quantity_item_properties ("qel:item_type" VARCHAR)')
    con.execute(
        'CREATE TABLE quantity_operations ("ocel:eid" VARCHAR, "ocel:oid" VARCHAR, '
        '"qel:item_type" VARCHAR, "qel:quantity" DOUBLE)'
    )

    # What every machine uses per quarter hour. Lines, halls and the plant read the
    # sum of what is in them plus a base load; only 500 machines have a meter.
    con.execute("""
        CREATE TEMP TABLE used AS
        SELECT m, s, 1 + (hash(m, s) % 100) / 20.0 AS q
        FROM range(1, 2001) t(m), range(0, 2880) u(s)
    """)
    con.execute(
        "CREATE TEMP TABLE line_used AS "
        "SELECT (m - 1) // 20 + 1 AS l, s, sum(q) + 3 AS q FROM used GROUP BY 1, 2"
    )
    con.execute(
        "CREATE TEMP TABLE hall_used AS "
        "SELECT (l - 1) // 10 + 1 AS h, s, sum(q) + 25 AS q FROM line_used GROUP BY 1, 2"
    )
    con.execute(
        "CREATE TEMP TABLE plant_used AS SELECT s, sum(q) + 120 AS q FROM hall_used GROUP BY 1"
    )

    def at(slot: str) -> str:
        return (
            f"strftime(TIMESTAMP '2026-03-01 00:00:00' + to_seconds({slot} * 900), "
            "'%Y-%m-%dT%H:%M:%SZ')"
        )

    quarter, hour = f"{at('s')}, {at('(s + 1)')}", f"{at('s * 4')}, {at('(s * 4 + 4)')}"
    con.execute(f"""
        COPY (
            SELECT 'electricity' AS flow, format('M{{:04d}}', m) AS object, round(q, 3) AS quantity,
                   {at("s")} AS start_time, {at("(s + 1)")} AS end_time, NULL AS event
            FROM used WHERE m <= 500
            UNION ALL SELECT 'electricity', format('L{{:03d}}', l), round(q, 3), {quarter}, NULL
            FROM line_used
            UNION ALL SELECT 'electricity', format('H{{:02d}}', h), round(q, 3), {quarter}, NULL
            FROM hall_used
            UNION ALL SELECT 'electricity', 'PLANT', round(q, 3), {quarter}, NULL FROM plant_used
            UNION ALL SELECT 'natural_gas', format('H{{:02d}}', h), 40 + hash(h, s) % 30, {hour}, NULL
            FROM range(1, 11) t(h), range(0, 720) u(s)
            UNION ALL SELECT 'natural_gas', 'PLANT', 800, {hour}, NULL FROM range(0, 720) u(s)
            UNION ALL SELECT 'steel_sheet', format('W{{:07d}}', workpiece), 2 + (i % 40) / 10.0,
                   NULL, NULL, eid FROM happened WHERE activity = 2
            UNION ALL SELECT 'steel_scrap', format('M{{:04d}}', machine), -0.3, NULL, NULL, eid
            FROM happened WHERE activity = 3
            UNION ALL SELECT 'paint', format('W{{:07d}}', workpiece), 0.4, NULL, NULL, eid
            FROM happened WHERE activity = 6
        ) TO '{RECORDS}' (HEADER, DELIMITER ',')
    """)
    con.execute("CHECKPOINT")
    con.close()


def build_socel() -> None:
    """The sOCEL as the builder makes it, then the nesting the builder cannot set
    yet: each meter inside the meter of what it is part of."""
    SOCEL_LOG.unlink(missing_ok=True)

    class Uploads:
        def put(self, content: bytes) -> str:
            return "records"

        def get(self, upload_id: str) -> bytes | None:
            return RECORDS.read_bytes()

    class Store:
        def add(self, ocel: OCEL, name: str) -> str:
            ocel.to_duckdb(SOCEL_LOG)
            return name

    with OCEL.read_duckdb(LOG, read_only=True) as log:
        BuildSocel(
            classifier=DuckDbLogClassifier(),
            importer=DuckDbRecordImporter(),
            uploads=Uploads(),
            store=Store(),
        ).execute(
            BuildSocelCommand(
                ocel=log,
                name="large plant",
                activities=ACTIVITIES,
                object_types=OBJECT_TYPES,
                records=RecordsToImport(upload_id="records", flows=FLOWS),
            )
        )

    con = duckdb.connect(str(SOCEL_LOG))
    con.execute("""
        INSERT INTO socel_containedin (flow_id, object_id, parent_object_id)
        SELECT metered.flow_id, part."ocel:oid_1", part."ocel:oid_2"
        FROM o2o part
        JOIN (SELECT DISTINCT flow_id, object_id FROM socel_interval_records) metered
          ON metered.object_id = part."ocel:oid_1"
        SEMI JOIN (SELECT DISTINCT flow_id, object_id FROM socel_interval_records) around
          ON around.flow_id = metered.flow_id AND around.object_id = part."ocel:oid_2"
        WHERE part."ocel:qualifier" = 'part_of'
    """)
    con.execute("CHECKPOINT")
    con.close()
    with OCEL.read_duckdb(SOCEL_LOG, read_only=True) as built:
        SOCEL.from_ocel(built).close()


def register() -> None:
    index = DATA / "event_logs.json"
    listed = json.loads(index.read_text())
    wanted = [
        {"key": "large-plant", "name": "Large Plant", "version": "1", "file": LOG.name},
        {
            "key": "large-plant-socel",
            "name": "Large Plant sOCEL",
            "version": "1",
            "file": SOCEL_LOG.name,
        },
    ]
    known = {entry["key"] for entry in listed["event_logs"]}
    listed["event_logs"] += [entry for entry in wanted if entry["key"] not in known]
    index.write_text(json.dumps(listed, indent="\t") + "\n")


if __name__ == "__main__":
    for step in (generate_log_and_records, build_socel):
        started = time.time()
        step()
        print(f"{step.__name__}: {time.time() - started:.0f} s")
    for path in (LOG, RECORDS, SOCEL_LOG):
        print(f"  {path.relative_to(DATA.parent)}  {path.stat().st_size / 1e6:.0f} MB")
    if "--register" in sys.argv:
        register()
        print("listed in data/event_logs.json; restart the backend to see them")
