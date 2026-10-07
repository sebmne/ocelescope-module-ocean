from dataclasses import dataclass

from ocelescope_module_ocean.application.ports.emission_rules_repository import (
    EmissionRulesRepository,
)
from ocelescope_module_ocean.domain.models.emission_rule_drafts import EmissionRuleDraft


@dataclass(frozen=True, kw_only=True)
class GetEmissionRulesCommand:
    ocel_id: str


class GetEmissionRules:
    """The rules the user has defined for an OCEL, complete or not."""

    def __init__(self, *, emission_rules_repository: EmissionRulesRepository) -> None:
        self._emission_rules_repository = emission_rules_repository

    def execute(self, command: GetEmissionRulesCommand) -> tuple[EmissionRuleDraft, ...]:
        return self._emission_rules_repository.get(command.ocel_id)
