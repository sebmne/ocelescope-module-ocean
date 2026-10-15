from typing import Protocol

from ocelescope_module_socel.domain.models.log_classification import LogClassification


class LogClassifier(Protocol):
    """Read classification of the bound view, per activity and object type."""

    def read(self) -> LogClassification:
        """How the log's activities and object types are classified now."""
        ...
