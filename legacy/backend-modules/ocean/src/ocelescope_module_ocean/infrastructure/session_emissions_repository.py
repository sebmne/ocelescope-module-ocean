from ocelescope_backend.app.internal.session import Session

from ocelescope_module_ocean.domain.models.allocation import ObjectEmissions
from ocelescope_module_ocean.domain.models.emissions import ProcessEmissions
from ocelescope_module_ocean.infrastructure.session_state import ocean_state


class SessionEmissionsRepository:
    """EmissionsRepository backed by the Ocelescope session's module state."""

    def __init__(self, session: Session) -> None:
        self._state = ocean_state(session)

    def save(self, ocel_id: str, emissions: ProcessEmissions) -> None:
        self._state.emissions[ocel_id] = emissions
        self._state.object_emissions.pop(ocel_id, None)

    def get(self, ocel_id: str) -> ProcessEmissions | None:
        return self._state.emissions.get(ocel_id)

    def save_object_emissions(self, ocel_id: str, object_emissions: ObjectEmissions) -> None:
        self._state.object_emissions[ocel_id] = object_emissions

    def get_object_emissions(self, ocel_id: str) -> ObjectEmissions | None:
        return self._state.object_emissions.get(ocel_id)
