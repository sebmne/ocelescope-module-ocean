from ocelescope_module_socel.domain.models.base import Model


class TypeClassification(Model):
    """An activity or object type of a log: how many events or objects it has,
    and the socel_class they carry. None when they carry none, or not all the
    same one."""

    name: str
    count: int
    socel_class: str | None


class LogClassification(Model):
    """How a log's activities and object types are classified, most frequent first."""

    activities: tuple[TypeClassification, ...]
    object_types: tuple[TypeClassification, ...]
