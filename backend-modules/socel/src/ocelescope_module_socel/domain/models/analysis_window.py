from datetime import datetime
from typing import Self

from pydantic import model_validator

from ocelescope_module_socel.domain.models.base import Model


class AnalysisWindow(Model):
    """A half-open analysis interval [start, end)."""

    start: datetime
    end: datetime

    @model_validator(mode="after")
    def _increasing(self) -> Self:
        try:
            valid = self.start < self.end
        except TypeError as error:
            raise ValueError(
                "Analysis-window timestamps must use compatible time zones."
            ) from error
        if not valid:
            raise ValueError("An analysis window must start before it ends.")
        return self

    def contains(self, timestamp: datetime) -> bool:
        return self.start <= timestamp < self.end
