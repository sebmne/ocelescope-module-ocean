"""Flow-instance domain objects."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class FlowInstance:
    """A flow observed at an OCEL object: ``(object, flow)``."""

    object_id: str
    flow_id: str
