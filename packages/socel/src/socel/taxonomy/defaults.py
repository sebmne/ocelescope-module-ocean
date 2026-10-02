"""Taxonomies and signatures from Tables 4.3-4.5 of the thesis."""

from socel.taxonomy.collection import SOCELTaxonomies
from socel.taxonomy.model import Node, Taxonomy
from socel.taxonomy.signatures import (
    ClassDomain,
    ClassSignature,
    ExpectedFlow,
    FlowDirection,
    SignatureCatalog,
)

FLOW_CATEGORIES = Taxonomy(
    {
        "technosphere": [
            Node(
                "energy",
                [Node("electricity"), Node("thermal"), Node("fuel")],
            ),
            Node(
                "material",
                [
                    Node("workpiece"),
                    Node("auxiliary", [Node("gas")]),
                    Node("packaging"),
                    Node("water"),
                ],
            ),
            Node("service", [Node("transport"), Node("storage")]),
        ],
        "elementary": [Node("natural resource"), Node("emission")],
    }
)

OBJECT_CLASSES = Taxonomy(
    {
        "handling_units": [Node("hu")],
        "process_resources": [
            Node(
                "pr",
                [
                    Node("processing", [Node("thermal"), Node("mechanical")]),
                    Node("transport"),
                    Node("storage"),
                    Node("infrastructure"),
                ],
            )
        ],
    }
)

EVENT_CLASSES = Taxonomy(
    {
        "operations": [
            Node(
                "op",
                [
                    Node(
                        "manufacturing",
                        [
                            Node("primary"),
                            Node("forming"),
                            Node("separating"),
                            Node("joining"),
                            Node("thermal"),
                            Node("surface", [Node("cleaning"), Node("coating")]),
                        ],
                    ),
                    Node(
                        "logistics",
                        [Node("transport"), Node("storage"), Node("packaging")],
                    ),
                ],
            )
        ]
    }
)


def _expected(
    category_id: str,
    direction: FlowDirection,
    *,
    alternative_group: str | None = None,
    condition_category_id: str | None = None,
    note: str | None = None,
) -> ExpectedFlow:
    return ExpectedFlow(
        category_id,
        direction,
        alternative_group,
        condition_category_id,
        note,
    )


def _event_signature(class_id: str, *expected: ExpectedFlow) -> ClassSignature:
    return ClassSignature(ClassDomain.EVENT, class_id, expected)


def _object_signature(class_id: str, *expected: ExpectedFlow) -> ClassSignature:
    return ClassSignature(ClassDomain.OBJECT, class_id, expected)


_SIGNATURES = (
    _event_signature(
        "op.manufacturing",
        _expected("energy", FlowDirection.INPUT),
    ),
    _event_signature(
        "op.manufacturing.primary",
        _expected("material.workpiece", FlowDirection.INPUT),
        _expected(
            "material.workpiece",
            FlowDirection.OUTPUT,
            note="Residue.",
        ),
    ),
    _event_signature(
        "op.manufacturing.separating",
        _expected("material.auxiliary", FlowDirection.INPUT),
        _expected(
            "material.auxiliary.gas",
            FlowDirection.INPUT,
            note="For example oxygen.",
        ),
        _expected(
            "material.workpiece",
            FlowDirection.OUTPUT,
            note="Offcut.",
        ),
        _expected(
            "material.water",
            FlowDirection.OUTPUT,
            note="Discharge.",
        ),
    ),
    _event_signature(
        "op.manufacturing.joining",
        _expected("material.auxiliary", FlowDirection.INPUT),
    ),
    _event_signature(
        "op.manufacturing.surface.cleaning",
        _expected("material.water", FlowDirection.INPUT),
        _expected(
            "material.workpiece",
            FlowDirection.OUTPUT,
            note="Scale.",
        ),
        _expected("material.water", FlowDirection.OUTPUT),
    ),
    _event_signature(
        "op.manufacturing.surface.coating",
        _expected(
            "material.auxiliary",
            FlowDirection.INPUT,
            note="Coating material.",
        ),
    ),
    _event_signature(
        "op.logistics.transport",
        _expected(
            "energy",
            FlowDirection.INPUT,
            alternative_group="transport-quantity",
            note="Fuel or electricity per instance.",
        ),
        _expected(
            "service.transport",
            FlowDirection.OUTPUT,
            alternative_group="transport-quantity",
            note="Transport service quantity, such as tonne-kilometers.",
        ),
    ),
    _event_signature(
        "op.logistics.storage",
        _expected(
            "service.storage",
            FlowDirection.OUTPUT,
            note="Dwell.",
        ),
    ),
    _event_signature(
        "op.logistics.packaging",
        _expected("material.packaging", FlowDirection.INPUT),
    ),
    _object_signature(
        "pr.processing",
        _expected("energy", FlowDirection.INPUT),
    ),
    _object_signature(
        "pr.processing.thermal",
        _expected(
            "energy.fuel",
            FlowDirection.INPUT,
            alternative_group="energy-source",
        ),
        _expected(
            "energy.electricity",
            FlowDirection.INPUT,
            alternative_group="energy-source",
        ),
        _expected(
            "emission",
            FlowDirection.OUTPUT,
            condition_category_id="energy.fuel",
            note="Combustion emissions if fuel is used.",
        ),
    ),
    _object_signature(
        "pr.processing.mechanical",
        _expected("energy.electricity", FlowDirection.INPUT),
    ),
    _object_signature(
        "pr.transport",
        _expected(
            "energy.fuel",
            FlowDirection.INPUT,
            alternative_group="energy-source",
        ),
        _expected(
            "energy.electricity",
            FlowDirection.INPUT,
            alternative_group="energy-source",
        ),
        _expected(
            "emission",
            FlowDirection.OUTPUT,
            condition_category_id="energy.fuel",
            note="Combustion emissions if fuel is used.",
        ),
    ),
    _object_signature(
        "pr.storage",
        _expected("energy.electricity", FlowDirection.INPUT),
    ),
    _object_signature(
        "pr.infrastructure",
        _expected("energy.electricity", FlowDirection.INPUT),
        _expected("material.water", FlowDirection.INPUT),
        _expected("material.water", FlowDirection.OUTPUT),
    ),
)

SIGNATURES = SignatureCatalog(
    FLOW_CATEGORIES,
    OBJECT_CLASSES,
    EVENT_CLASSES,
    _SIGNATURES,
)

DEFAULT_TAXONOMY = SOCELTaxonomies(
    flow_categories=FLOW_CATEGORIES,
    object_classes=OBJECT_CLASSES,
    event_classes=EVENT_CLASSES,
    signatures=SIGNATURES,
)
