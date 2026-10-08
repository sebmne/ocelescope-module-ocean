from socel import DEFAULT_TAXONOMY, Node, SOCELTaxonomies, Taxonomy

from ocelescope_module_socel.application.command import Command
from ocelescope_module_socel.domain.models.class_taxonomy import ClassNode, ClassTaxonomies


class GetClassTaxonomiesCommand(Command):
    taxonomies: SOCELTaxonomies = DEFAULT_TAXONOMY


class GetClassTaxonomies:
    """The classes an sOCEL may give its events and its objects, and the
    categories it may give its flows, as trees."""

    def execute(self, command: GetClassTaxonomiesCommand) -> ClassTaxonomies:
        return ClassTaxonomies(
            event_classes=_trees(command.taxonomies.event_classes),
            object_classes=_trees(command.taxonomies.object_classes),
            flow_categories=_trees(command.taxonomies.flow_categories),
        )


def _trees(taxonomy: Taxonomy) -> tuple[ClassNode, ...]:
    return tuple(_node(root, None) for roots in taxonomy.trees.values() for root in roots)


def _node(node: Node, parent: str | None) -> ClassNode:
    path = node.value if parent is None else f"{parent}.{node.value}"
    return ClassNode(
        path=path,
        label=node.value,
        children=tuple(_node(child, path) for child in node.children),
    )
