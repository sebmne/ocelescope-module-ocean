"""Flow categories: the classes of flows (`socel_flow.category`).

Source: Heinisch (2026), Chapter 4.3. Aimed at primary foreground data of
gate-to-gate discrete manufacturing, especially energy and material consumption;
explicitly not a complete ontology of all LCA-relevant flows.
"""

from socel.taxonomy.tree import Taxonomy

FLOW_CATEGORIES = Taxonomy(
    "Flow categories",
    {
        # Technosphere exchanges.
        "energy": "Energy.",
        "energy.electricity": "Grid or site electricity.",
        "energy.thermal": "Delivered heat or steam.",
        "energy.fuel": "Natural gas, diesel, etc.",
        "material": "Material.",
        "material.workpiece": "Material that constitutes or becomes a handling unit.",
        "material.auxiliary": "Cutting fluid, tool wear, etc.",
        "material.auxiliary.gas": "Oxygen, nitrogen, compressed air.",
        "material.packaging": "Cardboard, pallets.",
        "material.water": "Network water, intake or discharge.",
        "service": "Service.",
        "service.transport": "Inter-site transport, e.g. tonne-kilometres.",
        "service.storage": "Buffer or warehouse dwell.",
        # Elementary exchanges.
        "natural resource": "E.g. river or well cooling-water intake.",
        "emission": "E.g. combustion emissions.",
    },
)
