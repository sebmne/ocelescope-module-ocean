"""The sOCEL taxonomy, shared by preparation, conformance, and the API.

Define only local node names below. Nesting supplies each node's full path.
"""

from ocelescope_module_socel.domain.models.class_taxonomy import ClassNode, ClassTaxonomies

HANDLING_UNIT_ROOT = ClassNode(label="hu")
OPERATION_ROOT = ClassNode(
    label="op",
    children=(
        ClassNode(
            label="manufacturing",
            children=(
                ClassNode(label="primary"),
                ClassNode(label="forming"),
                ClassNode(label="separating"),
                ClassNode(label="joining"),
                ClassNode(label="thermal"),
                ClassNode(
                    label="surface",
                    children=(ClassNode(label="cleaning"), ClassNode(label="coating")),
                ),
            ),
        ),
        ClassNode(
            label="logistics",
            children=(
                ClassNode(label="transport"),
                ClassNode(label="storage"),
                ClassNode(label="packaging"),
            ),
        ),
    ),
)
TAXONOMY = ClassTaxonomies(
    event_classes=(OPERATION_ROOT,),
    object_classes=(
        HANDLING_UNIT_ROOT,
        ClassNode(
            label="pr",
            children=(
                ClassNode(
                    label="processing",
                    children=(ClassNode(label="thermal"), ClassNode(label="mechanical")),
                ),
                ClassNode(label="transport"),
                ClassNode(label="storage"),
                ClassNode(label="infrastructure"),
            ),
        ),
    ),
    flow_categories=(
        ClassNode(
            label="energy",
            children=(
                ClassNode(label="electricity"),
                ClassNode(label="thermal"),
                ClassNode(label="fuel"),
            ),
        ),
        ClassNode(
            label="material",
            children=(
                ClassNode(label="workpiece"),
                ClassNode(label="auxiliary", children=(ClassNode(label="gas"),)),
                ClassNode(label="packaging"),
                ClassNode(label="water"),
            ),
        ),
        ClassNode(
            label="service", children=(ClassNode(label="transport"), ClassNode(label="storage"))
        ),
        ClassNode(label="natural resource"),
        ClassNode(label="emission"),
    ),
)
