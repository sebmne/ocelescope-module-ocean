from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class EventAttribute:
    """An attribute of the rule's events."""

    name: str


@dataclass(frozen=True, kw_only=True)
class ObjectAttribute:
    """An attribute of the objects of one type related to the rule's events.

    Its value is the one the object had at the time of each event.
    """

    object_type: str
    name: str
    # Only relations with this qualifier; None means any.
    qualifier: str | None = None


AttributeRef = EventAttribute | ObjectAttribute
