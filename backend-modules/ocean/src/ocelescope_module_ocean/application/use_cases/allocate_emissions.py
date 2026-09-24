from dataclasses import dataclass

from ocelescope import OCEL

from ocelescope_module_ocean.application.ports.emissions_repository import EmissionsRepository
from ocelescope_module_ocean.domain.exceptions import EmissionsNotComputedError
from ocelescope_module_ocean.domain.models.allocation import AllocationConfig, AllocationSummary
from ocelescope_module_ocean.domain.services.allocation import allocate, summarize_allocation


@dataclass(frozen=True, kw_only=True)
class AllocateEmissionsCommand:
    ocel_id: str
    config: AllocationConfig


class AllocateEmissions:
    """Allocates the OCEL's computed emissions to its target objects and keeps the result."""

    def __init__(self, *, ocel: OCEL, emissions_repository: EmissionsRepository) -> None:
        self._ocel = ocel
        self._emissions_repository = emissions_repository

    def execute(self, command: AllocateEmissionsCommand) -> AllocationSummary:
        """Raises:
        EmissionsNotComputedError: There are no emissions to allocate yet.
        NoTargetObjectsError: The target object types have no objects.
        """
        emissions = self._emissions_repository.get(command.ocel_id)
        if emissions is None:
            raise EmissionsNotComputedError("Compute emissions before allocating them.")

        # TODO: resource types from the configuration page; until then all
        # object types are handling units, like in the original OCEAn.
        object_emissions = allocate(self._ocel, emissions, command.config)
        self._emissions_repository.save_object_emissions(command.ocel_id, object_emissions)
        return summarize_allocation(object_emissions)
