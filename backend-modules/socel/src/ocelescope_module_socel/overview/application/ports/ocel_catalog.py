from typing import Protocol


class OcelCatalog(Protocol):
    """The user's OCELs, by id."""

    def name(self, ocel_id: str) -> str: ...
