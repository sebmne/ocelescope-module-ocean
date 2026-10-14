from typing import Protocol

from ocelescope import OCEL


class LogStore(Protocol):
    """Where the user's logs are kept."""

    def add(self, ocel: OCEL, name: str) -> str:
        """Keep the log under the name; returns its id."""
        ...

    def get(self, ocel_id: str) -> OCEL:
        """The log as it is kept, without the filters the app shows it through."""
        ...

    def replace(self, ocel_id: str, ocel: OCEL) -> None:
        """Keep the given log in place of the one with the id: same id and name,
        so the app goes on showing, filtering and exporting it."""
        ...
