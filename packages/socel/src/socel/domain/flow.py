"""Sustainability-flow domain objects."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Flow:
    """A declared sustainability flow."""

    id: str
    unit: str
    category: str | None = None
    external_ref: str | None = None
