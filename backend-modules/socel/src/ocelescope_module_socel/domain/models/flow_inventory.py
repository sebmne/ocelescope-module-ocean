from ocelescope_module_socel.domain.models.base import Model


class FlowInstanceSummary(Model):
    """A flow observed at an object, where it sits among the metering scopes, and
    how many records it has."""

    object_id: str
    object_type: str
    # The flow instance of the same flow this one reports within, if any.
    parent_object_id: str | None
    interval_records: int
    event_records: int


class FlowSummary(Model):
    flow_id: str
    unit: str
    category: str | None
    external_ref: str | None
    instances: tuple[FlowInstanceSummary, ...]
