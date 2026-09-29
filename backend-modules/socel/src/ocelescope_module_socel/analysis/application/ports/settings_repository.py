from typing import Protocol

from ocelescope_module_socel.analysis.domain.models.analysis_settings import AnalysisSettings


class SettingsRepository(Protocol):
    """The analysis settings of the user's OCELs."""

    def get(self, ocel_id: str) -> AnalysisSettings: ...

    def save(self, ocel_id: str, settings: AnalysisSettings) -> None: ...
