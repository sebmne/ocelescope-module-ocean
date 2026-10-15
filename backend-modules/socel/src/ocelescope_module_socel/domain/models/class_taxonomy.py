from ocelescope_module_socel.domain.models.base import Model


class ClassNode(Model):
    """One local name in a taxonomy tree and the classes below it."""

    label: str
    children: tuple["ClassNode", ...] = ()

    def paths(self, parent_path: str = "") -> tuple[str, ...]:
        """Reconstruct this branch's paths from local names and an optional parent."""
        path = f"{parent_path}.{self.label}" if parent_path else self.label
        return (path, *(descendant for child in self.children for descendant in child.paths(path)))

    def contains(self, path: str) -> bool:
        """Match an exact path starting at this node, including intermediate nodes."""
        label, separator, remainder = path.partition(".")
        return label == self.label and (
            not separator or any(child.contains(remainder) for child in self.children)
        )


class ClassTaxonomies(Model):
    """The classes an sOCEL may give its events and its objects, and the
    categories it may give its flows, as trees."""

    event_classes: tuple[ClassNode, ...]
    object_classes: tuple[ClassNode, ...]
    flow_categories: tuple[ClassNode, ...]
