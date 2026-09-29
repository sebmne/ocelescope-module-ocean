from ocelescope_backend.app.internal.session import Session

from ocelescope_module_socel.analysis.domain.models.analysis_settings import AnalysisSettings
from ocelescope_module_socel.analysis.infrastructure.session_state import analysis_state


class SessionSettingsRepository:
    """SettingsRepository backed by the Ocelescope session's module state."""

    def __init__(self, session: Session) -> None:
        self._state = analysis_state(session)

    def get(self, ocel_id: str) -> AnalysisSettings:
        return self._state.settings.get(ocel_id, AnalysisSettings())

    def save(self, ocel_id: str, settings: AnalysisSettings) -> None:
        self._state.settings[ocel_id] = settings
