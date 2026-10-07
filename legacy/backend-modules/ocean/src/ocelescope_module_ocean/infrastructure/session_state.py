from dataclasses import dataclass, field

from ocelescope_backend.app.internal.session import Session

from ocelescope_module_ocean.domain.models.allocation import ObjectEmissions
from ocelescope_module_ocean.domain.models.emission_rule_drafts import EmissionRuleDraft
from ocelescope_module_ocean.domain.models.emissions import ProcessEmissions

_STATE_KEY = "ocean"


@dataclass
class OceanState:
    """What OCEAn keeps in a user's session, per OCEL id. Lost when the backend restarts."""

    rule_drafts: dict[str, tuple[EmissionRuleDraft, ...]] = field(default_factory=dict)
    emissions: dict[str, ProcessEmissions] = field(default_factory=dict)
    object_emissions: dict[str, ObjectEmissions] = field(default_factory=dict)


def ocean_state(session: Session) -> OceanState:
    """The session's OCEAn state, shared by all repositories of this session."""
    return session.get_module_state(_STATE_KEY, OceanState)
