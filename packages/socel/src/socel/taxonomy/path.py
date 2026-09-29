from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from socel.errors import InvalidClassError


@dataclass(frozen=True, order=True)
class TaxonomyPath:
    """A class or flow category: a dot-separated path in a tree, e.g. `pr.processing.thermal`.

    Comparison is case-sensitive. The first segment names the broad membership
    (`op`, `pr`, `hu`, `energy`, ...); each further segment narrows it down.
    """

    value: str

    def __post_init__(self) -> None:
        if not self.value or any(not part.strip() for part in self.value.split(".")):
            raise InvalidClassError(f"Not a dot-separated class path: {self.value!r}")

    @property
    def parts(self) -> tuple[str, ...]:
        return tuple(self.value.split("."))

    @property
    def depth(self) -> int:
        return len(self.parts)

    @property
    def root(self) -> TaxonomyPath:
        return TaxonomyPath(self.parts[0])

    @property
    def parent(self) -> TaxonomyPath | None:
        return TaxonomyPath(".".join(self.parts[:-1])) if self.depth > 1 else None

    def ancestors(self) -> tuple[TaxonomyPath, ...]:
        """From the root down to, and including, this path."""
        return tuple(TaxonomyPath(".".join(self.parts[:n])) for n in range(1, self.depth + 1))

    def is_a(self, other: TaxonomyPath | str) -> bool:
        """Whether this path is `other` or lies below it: `pr.processing.thermal` is a `pr`."""
        other = TaxonomyPath.of(other)
        return self.parts[: other.depth] == other.parts

    @staticmethod
    def of(value: TaxonomyPath | str) -> TaxonomyPath:
        return value if isinstance(value, TaxonomyPath) else TaxonomyPath(value)

    @staticmethod
    def common_ancestor(paths: Iterable[TaxonomyPath | str]) -> TaxonomyPath | None:
        """The most specific path all given paths lie below, or None if they share no root.

        E.g. `pr.processing.thermal` and `pr.processing.mechanical` share
        `pr.processing`: the right class for an object type holding both.
        """
        parts_list = [TaxonomyPath.of(path).parts for path in paths]
        if not parts_list:
            return None
        shared: list[str] = []
        for segments in zip(*parts_list, strict=False):
            if len(set(segments)) != 1:
                break
            shared.append(segments[0])
        return TaxonomyPath(".".join(shared)) if shared else None

    def __str__(self) -> str:
        return self.value
