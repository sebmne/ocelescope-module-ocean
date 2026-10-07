from dataclasses import dataclass

from ocelescope_module_ocean.application.ports.emissions_repository import EmissionsRepository
from ocelescope_module_ocean.domain.models.allocation import AllocationSummary
from ocelescope_module_ocean.domain.services.allocation import summarize_allocation


@dataclass(frozen=True, kw_only=True)
class GetObjectEmissionsCommand:
    ocel_id: str


class GetObjectEmissions:
    """The current allocation of the OCEL's emissions, if there is one."""

    def __init__(self, *, emissions_repository: EmissionsRepository) -> None:
        self._emissions_repository = emissions_repository

    def execute(self, command: GetObjectEmissionsCommand) -> AllocationSummary | None:
        object_emissions = self._emissions_repository.get_object_emissions(command.ocel_id)
        return summarize_allocation(object_emissions) if object_emissions else None
