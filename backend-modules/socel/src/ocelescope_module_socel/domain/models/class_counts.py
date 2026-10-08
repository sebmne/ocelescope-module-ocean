from ocelescope_module_socel.domain.models.base import Model


class ClassCount(Model):
    """How many objects or events carry a socel_class (None: unclassified).

    `is_core` marks the classes that make handling units (for objects) or
    operations (for events).
    """

    socel_class: str | None
    count: int
    is_core: bool


class ClassCounts(Model):
    objects: tuple[ClassCount, ...]
    events: tuple[ClassCount, ...]
