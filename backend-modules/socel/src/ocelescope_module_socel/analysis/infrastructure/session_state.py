from dataclasses import dataclass, field

from ocelescope_backend.app.internal.session import Session

from ocelescope_module_socel.analysis.domain.models.analysis_settings import AnalysisSettings

_STATE_KEY = "socel-analysis"


@dataclass
class AnalysisState:
    """What the analysis keeps in a user's session, per OCEL id. Lost when the
    backend restarts."""

    settings: dict[str, AnalysisSettings] = field(default_factory=dict)


def analysis_state(session: Session) -> AnalysisState:
    """The session's analysis state, shared by all repositories of this session."""
    return session.get_module_state(_STATE_KEY, AnalysisState)
