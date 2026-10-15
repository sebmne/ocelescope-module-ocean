from dataclasses import dataclass

from ocelescope_module_socel.application.ports.log_classifier import LogClassifier
from ocelescope_module_socel.domain.models.log_classification import LogClassification


@dataclass(frozen=True, kw_only=True)
class GetLogClassificationCommand:
    pass


class GetLogClassification:
    """How a log's activities and object types are classified now. Any log may
    be asked, an sOCEL or not."""

    def __init__(self, *, classifier: LogClassifier) -> None:
        self._classifier = classifier

    def execute(self, command: GetLogClassificationCommand) -> LogClassification:
        return self._classifier.read()
