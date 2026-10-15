from dataclasses import dataclass

from ocelescope_module_socel.domain.models.class_taxonomy import ClassTaxonomies
from ocelescope_module_socel.domain.taxonomies import TAXONOMY


@dataclass(frozen=True, kw_only=True)
class GetClassTaxonomiesCommand:
    pass


class GetClassTaxonomies:
    def execute(self, command: GetClassTaxonomiesCommand) -> ClassTaxonomies:
        return TAXONOMY
