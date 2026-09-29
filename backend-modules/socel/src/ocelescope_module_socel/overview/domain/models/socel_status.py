from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, kw_only=True)
class SocelStatus:
    """Whether an OCEL is an sOCEL - it has the sOCEL tables - and what it holds.

    Handling units and operations come from the reserved attributes, so a plain
    OCEL can have them too. Says nothing about conformance: that takes a validation.
    """

    ocel_name: str
    is_socel: bool
    objects: int
    events: int
    handling_units: int
    operations: int
    flows: int = 0
    flow_instances: int = 0
    interval_records: int = 0
    event_records: int = 0
    containments: int = 0
    # The period the flow records span, in UTC; None without records with a time.
    records_from: datetime | None = None
    records_to: datetime | None = None
