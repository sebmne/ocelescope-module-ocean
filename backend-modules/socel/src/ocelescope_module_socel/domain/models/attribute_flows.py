from typing import Literal

from ocelescope_module_socel.domain.models.base import Model

# Which way an attribute's amounts flow, seen from the object they are recorded
# at: into it (stored as they are) or out of it (stored negative).
type Direction = Literal["in", "out"]


class AttributeFlow(Model):
    """An event attribute taken as a flow: each value becomes a record of
    `flow_id` at the event, observed at the event's objects of `object_type`
    (split equally if there are several).

    An sOCEL quantity is signed: positive into the object, negative out of it.
    An attribute usually holds amounts, so `direction` says which way they
    flow; for "out" they are stored negative. A value that is negative already
    is taken as it is."""

    attribute: str
    flow_id: str
    object_type: str
    direction: Direction = "in"
