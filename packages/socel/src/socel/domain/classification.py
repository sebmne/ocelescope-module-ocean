"""sOCEL classifications of OCEL objects and events."""

from dataclasses import dataclass
from typing import Literal

type ClassifiedElement = Literal["object", "event"]


@dataclass(frozen=True, slots=True)
class Classification:
    """The sOCEL class assigned to an OCEL object or event."""

    element: ClassifiedElement
    element_id: str
    name: str
