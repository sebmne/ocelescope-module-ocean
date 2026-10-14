from collections.abc import Sequence
from typing import Protocol

from ocelescope import OCEL

from ocelescope_module_socel.domain.models.containment import TypeContainment


class ContainmentWriter(Protocol):
    """Writes which flow instance lies inside which, from containment between object types."""

    def write(self, ocel: OCEL, containments: Sequence[TypeContainment]) -> None:
        """Adds a row to the log's containment for every pair of objects the
        relations of the containments connect, per flow of each.

        Raises:
            SeveralParents: If an object would lie inside two objects for one flow.
        """
        ...
