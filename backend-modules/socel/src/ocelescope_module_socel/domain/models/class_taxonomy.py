from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ClassNode:
    """One class of a taxonomy: its full path (e.g. "op.manufacturing.joining"),
    its own name within its parent ("joining"), and the classes below it."""

    path: str
    label: str
    children: tuple["ClassNode", ...]


@dataclass(frozen=True, kw_only=True)
class ClassTaxonomies:
    """The classes an sOCEL may give its events and its objects, and the
    categories it may give its flows, as trees."""

    event_classes: tuple[ClassNode, ...]
    object_classes: tuple[ClassNode, ...]
    flow_categories: tuple[ClassNode, ...]
