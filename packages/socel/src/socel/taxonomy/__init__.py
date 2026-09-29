"""The sOCEL taxonomies, one tree per kind of thing classified.

Events are classified as operations; objects as handling units or process
resources; flows by category. Knowledge about the domain, kept as data: it
classifies and sets expectations, but never decides whether an sOCEL conforms.
"""

from socel.taxonomy.flows import FLOW_CATEGORIES
from socel.taxonomy.handling_units import HANDLING_UNITS
from socel.taxonomy.operations import OPERATIONS
from socel.taxonomy.path import TaxonomyPath
from socel.taxonomy.process_resources import PROCESS_RESOURCES
from socel.taxonomy.tree import Node, Taxonomy

# What each entity's socel_class may be.
EVENT_CLASSES: tuple[Taxonomy, ...] = (OPERATIONS,)
OBJECT_CLASSES: tuple[Taxonomy, ...] = (HANDLING_UNITS, PROCESS_RESOURCES)

__all__ = [
    "EVENT_CLASSES",
    "FLOW_CATEGORIES",
    "HANDLING_UNITS",
    "OBJECT_CLASSES",
    "OPERATIONS",
    "PROCESS_RESOURCES",
    "Node",
    "Taxonomy",
    "TaxonomyPath",
]
