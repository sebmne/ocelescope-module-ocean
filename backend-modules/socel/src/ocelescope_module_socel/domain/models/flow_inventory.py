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


class FlowInstanceRow(Model):
    """A flow at one object: the object it lies inside, how many lie directly
    inside it, its records, and the quantity they sum to."""

    object_id: str
    object_type: str
    parent_object_id: str | None
    contains: int
    interval_records: int
    event_records: int
    quantity: float


class FlowInstancePage(Model):
    """One page of a flow's instances: the rows, how many there are in all under
    the same filter, and, when the page shows what lies inside an object, the
    way from the outermost object down to it."""

    total: int
    rows: tuple[FlowInstanceRow, ...]
    path: tuple[str, ...]
