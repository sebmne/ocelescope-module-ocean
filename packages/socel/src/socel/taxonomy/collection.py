"""The complete set of taxonomies used by an sOCEL view."""

from dataclasses import dataclass

from socel.taxonomy.model import Taxonomy
from socel.taxonomy.signatures import SignatureCatalog


@dataclass(frozen=True, slots=True)
class SOCELTaxonomies:
    flow_categories: Taxonomy
    object_classes: Taxonomy
    event_classes: Taxonomy
    signatures: SignatureCatalog
