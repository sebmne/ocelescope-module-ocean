from dataclasses import dataclass, field

from ocelescope_backend.app.internal.session import Session

from ocelescope_module_ocean.domain.models.allocation import ObjectEmissions
from ocelescope_module_ocean.domain.models.emissions import ProcessEmissions

_STATE_KEY = "ocean"


@dataclass
class _OceanState:
    """What OCEAn keeps in a user's session. Lost when the backend restarts."""

    emissions: dict[str, ProcessEmissions] = field(default_factory=dict)
    object_emissions: dict[str, ObjectEmissions] = field(default_factory=dict)


class SessionEmissionsRepository:
    """EmissionsRepository backed by the Ocelescope session's module state."""

    def __init__(self, session: Session) -> None:
        self._state = session.get_module_state(_STATE_KEY, _OceanState)

    def save(self, ocel_id: str, emissions: ProcessEmissions) -> None:
        self._state.emissions[ocel_id] = emissions
        self._state.object_emissions.pop(ocel_id, None)

    def get(self, ocel_id: str) -> ProcessEmissions | None:
        return self._state.emissions.get(ocel_id)

    def save_object_emissions(self, ocel_id: str, object_emissions: ObjectEmissions) -> None:
        self._state.object_emissions[ocel_id] = object_emissions

    def get_object_emissions(self, ocel_id: str) -> ObjectEmissions | None:
        return self._state.object_emissions.get(ocel_id)
