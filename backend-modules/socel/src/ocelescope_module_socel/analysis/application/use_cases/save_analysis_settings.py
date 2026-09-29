from dataclasses import dataclass

from ocelescope_module_socel.analysis.application.ports.settings_repository import (
    SettingsRepository,
)
from ocelescope_module_socel.analysis.domain.models.analysis_settings import AnalysisSettings


@dataclass(frozen=True, kw_only=True)
class SaveAnalysisSettingsCommand:
    ocel_id: str
    settings: AnalysisSettings


class SaveAnalysisSettings:
    """Replaces the OCEL's analysis settings."""

    def __init__(self, *, settings: SettingsRepository) -> None:
        self._settings = settings

    def execute(self, command: SaveAnalysisSettingsCommand) -> AnalysisSettings:
        self._settings.save(command.ocel_id, command.settings)
        return command.settings
