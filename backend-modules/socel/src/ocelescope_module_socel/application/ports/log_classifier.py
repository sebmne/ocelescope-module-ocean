from collections.abc import Mapping
from typing import Protocol

from ocelescope import OCEL

from ocelescope_module_socel.domain.models.log_classification import LogClassification


class LogClassifier(Protocol):
    """Reads and writes the socel_class of a log's events and objects, per
    activity and per object type."""

    def read(self, ocel: OCEL) -> LogClassification:
        """How the log's activities and object types are classified now."""
        ...

    def classify(
        self,
        ocel: OCEL,
        *,
        activities: Mapping[str, str | None],
        object_types: Mapping[str, str | None],
    ) -> OCEL:
        """A copy of the log with the sOCEL tables, in which the events of each
        named activity and the objects of each named object type carry the given
        class (None: no class). Types not named keep what they have. The log
        itself stays untouched."""
        ...
