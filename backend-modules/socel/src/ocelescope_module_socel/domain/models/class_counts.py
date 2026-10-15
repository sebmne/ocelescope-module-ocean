from ocelescope_module_socel.domain.models.base import Model


class ClassCount(Model):
    """How many objects or events carry a full class path (None: unclassified)."""

    socel_class: str | None
    count: int


class ClassCounts(Model):
    objects: tuple[ClassCount, ...]
    events: tuple[ClassCount, ...]
