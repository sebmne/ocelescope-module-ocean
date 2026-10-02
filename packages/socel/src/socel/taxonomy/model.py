"""Small tree structures for sOCEL taxonomies."""

from collections.abc import Iterator
from dataclasses import dataclass, field


@dataclass(slots=True)
class Node:
    """One local value in a taxonomy tree."""

    value: str
    children: list["Node"] = field(default_factory=list)


@dataclass(slots=True)
class Taxonomy:
    """Named trees whose node paths are dot-separated sOCEL identifiers."""

    trees: dict[str, list[Node]] = field(default_factory=dict)

    def __iter__(self) -> Iterator[str]:
        """Yield all encoded paths in definition order."""
        for roots in self.trees.values():
            for root in roots:
                yield from self._paths(root)

    def __len__(self) -> int:
        return sum(1 for _ in self)

    def __contains__(self, path: object) -> bool:
        return isinstance(path, str) and self.find(path) is not None

    def find(self, path: str) -> Node | None:
        """Find the node addressed by a dot-separated path."""
        result = self._locate(path)
        return result[1] if result is not None else None

    def resolve(self, path: str | None) -> Node | None:
        """Resolve a stored identifier without rejecting custom values."""
        return self.find(path) if path is not None else None

    def require(self, path: str) -> Node:
        """Return a known node or raise a descriptive error."""
        node = self.find(path)
        if node is None:
            raise KeyError(f"Unknown taxonomy path {path!r}.")
        return node

    def tree_name(self, path: str) -> str | None:
        """Return the name of the tree containing a path."""
        result = self._locate(path)
        return result[0] if result is not None else None

    def _locate(self, path: str) -> tuple[str, Node] | None:
        parts = path.split(".")
        if not parts or any(not part for part in parts):
            return None

        for name, roots in self.trees.items():
            node = self._find_child(roots, parts[0])
            for part in parts[1:]:
                if node is None:
                    break
                node = self._find_child(node.children, part)
            if node is not None:
                return name, node
        return None

    def children(self, path: str) -> list[str]:
        """Return the encoded paths of the direct children of a path."""
        node = self.require(path)
        return [f"{path}.{child.value}" for child in node.children]

    def ancestors(self, path: str) -> list[str]:
        """Return parent paths from the direct parent up to the root."""
        self.require(path)
        parts = path.split(".")
        return [".".join(parts[:end]) for end in range(len(parts) - 1, 0, -1)]

    def descendants(self, path: str) -> list[str]:
        """Return descendant paths in depth-first definition order."""
        node = self.require(path)
        descendants: list[str] = []

        def visit(parent: Node, parent_path: str) -> None:
            for child in parent.children:
                child_path = f"{parent_path}.{child.value}"
                descendants.append(child_path)
                visit(child, child_path)

        visit(node, path)
        return descendants

    def is_a(self, path: str, ancestor_path: str) -> bool:
        """Whether a path is or descends from another known path."""
        return (
            path in self
            and ancestor_path in self
            and (path == ancestor_path or ancestor_path in self.ancestors(path))
        )

    @classmethod
    def _paths(cls, node: Node, parent: str | None = None) -> Iterator[str]:
        path = node.value if parent is None else f"{parent}.{node.value}"
        yield path
        for child in node.children:
            yield from cls._paths(child, path)

    @staticmethod
    def _find_child(nodes: list[Node], value: str) -> Node | None:
        return next((node for node in nodes if node.value == value), None)
