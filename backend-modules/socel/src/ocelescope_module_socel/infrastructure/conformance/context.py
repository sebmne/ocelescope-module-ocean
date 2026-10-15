"""Data shared by all rules during one validation run."""

from collections.abc import Mapping
from dataclasses import dataclass

from ocelescope import OCEL


@dataclass(frozen=True)
class ValidationContext:
    ocel: OCEL
    columns: Mapping[str, Mapping[str, str]]
