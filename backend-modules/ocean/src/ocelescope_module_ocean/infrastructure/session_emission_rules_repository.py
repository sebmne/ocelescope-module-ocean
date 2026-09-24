from collections.abc import Sequence

from ocelescope_backend.app.internal.session import Session

from ocelescope_module_ocean.domain.models.emission_rule_drafts import EmissionRuleDraft
from ocelescope_module_ocean.infrastructure.session_state import ocean_state


class SessionEmissionRulesRepository:
    """EmissionRulesRepository backed by the Ocelescope session's module state."""

    def __init__(self, session: Session) -> None:
        self._state = ocean_state(session)

    def save(self, ocel_id: str, drafts: Sequence[EmissionRuleDraft]) -> None:
        self._state.rule_drafts[ocel_id] = tuple(drafts)

    def get(self, ocel_id: str) -> tuple[EmissionRuleDraft, ...]:
        return self._state.rule_drafts.get(ocel_id, ())
