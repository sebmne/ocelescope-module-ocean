from ocelescope_module_socel.domain.models.base import Model


class FlowByObjectType(Model):
    """A flow at the objects of one type: at how many of them it is observed
    (its flow instances there), how many of those lie inside another instance
    of the flow, and how many records they have."""

    object_type: str
    instances: int
    contained: int
    interval_records: int
    event_records: int


class FlowSummary(Model):
    """A flow with its counts over the whole log, and per object type."""

    flow_id: str
    unit: str
    category: str | None
    external_ref: str | None
    instances: int
    contained: int
    interval_records: int
    event_records: int
    by_object_type: tuple[FlowByObjectType, ...]
