"""Process resources: a class of objects (`socel_class` of objects), rooted at `pr`.

The objects that perform operations, e.g. furnaces, presses, trucks. Source:
Heinisch (2026), Chapter 4.4; their expected flows (Chapter 4.5) come with the
quality checks.
"""

from socel.taxonomy.tree import Taxonomy

PROCESS_RESOURCES = Taxonomy(
    "Process resources",
    {
        "pr": "Process resource: performs operations.",
        "pr.processing": "Performs processing; consumes energy.",
        "pr.processing.thermal": "Thermal processing, e.g. a furnace.",
        "pr.processing.mechanical": "Mechanical processing, e.g. a press.",
        "pr.processing.transport": "Transport equipment, e.g. a truck or crane.",
        "pr.processing.storage": "Storage equipment.",
        "pr.infrastructure": "Infrastructure, e.g. a building or site.",
    },
)
