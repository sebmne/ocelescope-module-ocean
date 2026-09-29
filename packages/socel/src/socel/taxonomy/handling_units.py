"""Handling units: a class of objects (`socel_class` of objects), rooted at `hu`.

The objects being processed, e.g. coils, slabs, orders. The thesis defines only
the root; subclasses (`hu.<subclass>`) are free to define per project.
"""

from socel.taxonomy.tree import Taxonomy

HANDLING_UNITS = Taxonomy(
    "Handling units",
    {"hu": "Handling unit: an object being processed."},
)
