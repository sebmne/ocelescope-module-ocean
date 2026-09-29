from __future__ import annotations

from collections.abc import Iterator, Mapping
from dataclasses import dataclass

from socel.taxonomy.path import TaxonomyPath


@dataclass(frozen=True)
class Node:
    path: TaxonomyPath
    description: str


class Taxonomy:
    """A tree of known classes (or flow categories), each described.

    Knowledge, not a rule: the thesis permits classes below a known node
    (`hu.<subclass>`), and an unknown or coarse class is a quality finding at
    most, never a conformance error.
    """

    def __init__(self, name: str, nodes: Mapping[str, str]) -> None:
        """nodes: path -> description. Every node's parent must be a node too."""
        self.name = name
        self._nodes = {
            path: Node(path, description)
            for path, description in ((TaxonomyPath(p), d) for p, d in nodes.items())
        }
        orphans = [
            str(node.path)
            for node in self._nodes.values()
            if node.path.parent is not None and node.path.parent not in self._nodes
        ]
        if orphans:
            raise ValueError(f"{name}: nodes without their parent: {', '.join(orphans)}")

    def __contains__(self, path: object) -> bool:
        if isinstance(path, str):
            path = TaxonomyPath(path)
        return path in self._nodes

    def __iter__(self) -> Iterator[Node]:
        return iter(self._nodes.values())

    def __getitem__(self, path: TaxonomyPath | str) -> Node:
        return self._nodes[TaxonomyPath.of(path)]

    def covers(self, path: TaxonomyPath | str) -> bool:
        """Whether `path` belongs to this taxonomy: a known node or a subclass of one,
        e.g. `hu.coil` belongs to the handling units though only `hu` is listed."""
        return self.known_ancestor(path) is not None

    @property
    def roots(self) -> tuple[Node, ...]:
        return tuple(node for node in self._nodes.values() if node.path.parent is None)

    def children(self, path: TaxonomyPath | str) -> tuple[Node, ...]:
        parent = TaxonomyPath.of(path)
        return tuple(node for node in self._nodes.values() if node.path.parent == parent)

    def known_ancestor(self, path: TaxonomyPath | str) -> Node | None:
        """The most specific known node `path` lies at or below, e.g. `hu` for `hu.coil`."""
        for ancestor in reversed(TaxonomyPath.of(path).ancestors()):
            if ancestor in self._nodes:
                return self._nodes[ancestor]
        return None
