from dataclasses import dataclass

from ocelescope import OCEL

from ocelescope_module_ocean.application.ports.emissions_repository import EmissionsRepository
from ocelescope_module_ocean.domain.models.emission_rules import EmissionRule
from ocelescope_module_ocean.domain.models.emissions import EmissionsOverview
from ocelescope_module_ocean.domain.services.emissions import compute_emissions, summarize_emissions


@dataclass(frozen=True, kw_only=True)
class ComputeEmissionsCommand:
    ocel_id: str
    rules: tuple[EmissionRule, ...]


class ComputeEmissions:
    """Applies the emission rules to the OCEL and keeps the result for later steps."""

    def __init__(self, *, ocel: OCEL, emissions_repository: EmissionsRepository) -> None:
        self._ocel = ocel
        self._emissions_repository = emissions_repository

    def execute(self, command: ComputeEmissionsCommand) -> EmissionsOverview:
        """Raises:
        InvalidEmissionRuleError: A rule does not fit the OCEL.
        """
        emissions = compute_emissions(self._ocel, command.rules)
        self._emissions_repository.save(command.ocel_id, emissions)
        return summarize_emissions(emissions)
