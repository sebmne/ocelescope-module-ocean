from datetime import datetime

from ocelescope_module_socel.domain.models.base import Model


class SocelStatus(Model):
    """What an sOCEL holds, in counts."""

    objects: int
    events: int
    handling_units: int
    operations: int
    flows: int
    flow_instances: int
    interval_records: int
    event_records: int
    containments: int
    # The period the flow records span, in UTC; None without records.
    records_from: datetime | None = None
    records_to: datetime | None = None
