from typing import Protocol

from ocelescope import OCEL


class LogStore(Protocol):
    """Where the user's logs are kept."""

    def add(self, ocel: OCEL, name: str) -> str:
        """Keep the log under the name; returns its id."""
        ...
