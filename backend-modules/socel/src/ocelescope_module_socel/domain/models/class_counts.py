from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class ClassCount:
    """How many objects or events carry a socel_class (None: unclassified).

    `is_core` marks the classes that make handling units (for objects) or
    operations (for events).
    """

    socel_class: str | None
    count: int
    is_core: bool


@dataclass(frozen=True, kw_only=True)
class ClassCounts:
    objects: tuple[ClassCount, ...]
    events: tuple[ClassCount, ...]
