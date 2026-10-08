from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class TypeClassification:
    """An activity or object type of a log: how many events or objects it has,
    and the socel_class they carry. None when they carry none, or not all the
    same one."""

    name: str
    count: int
    socel_class: str | None


@dataclass(frozen=True, kw_only=True)
class LogClassification:
    """How a log's activities and object types are classified, most frequent first."""

    activities: tuple[TypeClassification, ...]
    object_types: tuple[TypeClassification, ...]
