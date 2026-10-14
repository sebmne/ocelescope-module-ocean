from datetime import UTC, datetime

import polars as pl
from ocelescope import OCEL
from ocelescope.ocel.constants.pm4py import (
    ACTIVITY_COL,
    E2O_QUALIFIER,
    EID_COL,
    O2O_QUALIFIER,
    O2O_SOURCE_ID,
    O2O_TARGET_ID,
    OID_COL,
    OTYPE_COL,
    TIMESTAMP_COL,
)


def at(day: int, hour: int = 0) -> datetime:
    return datetime(2026, 1, day, hour, tzinfo=UTC)


def example_log() -> OCEL:
    """A plain OCEL of a small plant: two machines in one hall mill a part each,
    and both parts are shipped together. The mill events carry a numeric
    attribute, `coolant_l`."""
    return OCEL.from_frames(
        events=pl.DataFrame(
            {
                EID_COL: ["e1", "e2", "e3"],
                ACTIVITY_COL: ["mill", "mill", "ship"],
                TIMESTAMP_COL: [at(1, 10), at(2, 10), at(2, 12)],
                "coolant_l": [2.0, 3.0, None],
            }
        ),
        objects=pl.DataFrame(
            {
                OID_COL: ["hall-1", "m1", "m2", "p1", "p2"],
                OTYPE_COL: ["hall", "machine", "machine", "part", "part"],
            }
        ),
        relations=pl.DataFrame(
            {
                EID_COL: ["e1", "e1", "e2", "e2", "e3", "e3"],
                OID_COL: ["m1", "p1", "m2", "p2", "p1", "p2"],
                E2O_QUALIFIER: ["resource", "input", "resource", "input", "load", "load"],
            }
        ),
        o2o=pl.DataFrame(
            {
                O2O_SOURCE_ID: ["m1", "m2"],
                O2O_TARGET_ID: ["hall-1", "hall-1"],
                O2O_QUALIFIER: ["located_in", "located_in"],
            }
        ),
    )


# The classes every type of the example log gets when it becomes an sOCEL.
CLASSES = {
    "activities": {"mill": "op.manufacturing.separating", "ship": "op.logistics.transport"},
    "objectTypes": {
        "hall": "pr.infrastructure",
        "machine": "pr.processing.mechanical",
        "part": "hu",
    },
}

# A record file for the example log:
# - electricity as interval records at both machines and at the hall,
# - heat leaving m1 as a record of event e1 (negative: out of the object),
# - one row at an object the log does not have.
RECORDS_CSV = b"""flow,object,quantity,start,end,event
electricity,m1,24,2026-01-01T00:00:00Z,2026-01-02T00:00:00Z,
electricity,m2,12,2026-01-01T12:00:00Z,2026-01-02T12:00:00Z,
electricity,hall-1,100,2026-01-01T00:00:00Z,2026-01-03T00:00:00Z,
heat,m1,-5,,,e1
electricity,nowhere,1,2026-01-01T00:00:00Z,2026-01-01T01:00:00Z,
"""

MAPPING = {
    "flow": "flow",
    "object": "object",
    "quantity": "quantity",
    "startTime": "start",
    "endTime": "end",
    "event": "event",
}

FLOWS = {
    "electricity": {"unit": "kWh", "category": "energy.electricity"},
    "heat": {"unit": "kWh", "category": "energy.thermal"},
}

# The machines lie inside the hall for electricity, through their o2o relation.
CONTAINMENT = [
    {
        "objectType": "machine",
        "parentType": "hall",
        "qualifier": "located_in",
        "flows": ["electricity"],
    }
]
