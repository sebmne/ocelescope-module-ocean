"""Operations: the classes of events (`socel_class` of events), rooted at `op`.

Source: Heinisch (2026), Chapter 4.4. Classes group by expected flow behavior:
two operations share a class when they have the same expected flows and the same
handling-unit topology. Where DIN 8580 groups differently, this criterion wins:
reheating and heat treatment merge into `op.manufacturing.thermal`, and surface
treatment splits into cleaning and coating.

The expected flows per class (signatures, Chapter 4.5) belong to the quality
checks and are added with them.
"""

from socel.taxonomy.tree import Taxonomy

OPERATIONS = Taxonomy(
    "Operations",
    {
        "op": "Operation: uses at least one process resource.",
        "op.manufacturing": "Transforms handling units.",
        "op.manufacturing.primary": "Material becomes handling unit(s) and residue.",
        "op.manufacturing.forming": (
            "A handling unit becomes a handling unit; mass nominally conserved."
        ),
        "op.manufacturing.separating": "A handling unit becomes handling unit(s) and offcut.",
        "op.manufacturing.joining": "Handling units, optionally with filler, become one.",
        "op.manufacturing.thermal": "A handling unit becomes the same handling unit (heat).",
        "op.manufacturing.surface": "A handling unit remains; its surface changes.",
        "op.manufacturing.cleaning": "A handling unit is cleaned; consumes water, outputs scale.",
        "op.manufacturing.coating": "A handling unit plus coating material become a handling unit.",
        "op.logistics": "Relocates, holds, or packages handling units.",
        "op.logistics.transport": "Relocates handling units between sites.",
        "op.logistics.storage": "Holds handling units over time.",
        "op.logistics.packaging": "Changes the packaging state of handling units.",
    },
)
