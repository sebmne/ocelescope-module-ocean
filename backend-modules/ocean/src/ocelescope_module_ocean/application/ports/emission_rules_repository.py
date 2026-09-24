from collections.abc import Sequence
from typing import Protocol

from ocelescope_module_ocean.domain.models.emission_rule_drafts import EmissionRuleDraft


class EmissionRulesRepository(Protocol):
    """Keeps the rules the user is defining for each OCEL between visits."""

    def save(self, ocel_id: str, drafts: Sequence[EmissionRuleDraft]) -> None:
        """Replaces the OCEL's rules with `drafts`."""
        ...

    def get(self, ocel_id: str) -> tuple[EmissionRuleDraft, ...]:
        """The OCEL's rules; empty if none were defined yet."""
        ...
