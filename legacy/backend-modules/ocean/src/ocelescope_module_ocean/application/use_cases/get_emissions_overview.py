from dataclasses import dataclass

from ocelescope_module_ocean.application.ports.emissions_repository import EmissionsRepository
from ocelescope_module_ocean.domain.models.emissions import EmissionsOverview
from ocelescope_module_ocean.domain.services.emissions import summarize_emissions


@dataclass(frozen=True, kw_only=True)
class GetEmissionsOverviewCommand:
    ocel_id: str


class GetEmissionsOverview:
    """Summarizes the emissions computed for an OCEL."""

    def __init__(self, *, emissions_repository: EmissionsRepository) -> None:
        self._emissions_repository = emissions_repository

    def execute(self, command: GetEmissionsOverviewCommand) -> EmissionsOverview:
        return summarize_emissions(self._emissions_repository.get(command.ocel_id))
