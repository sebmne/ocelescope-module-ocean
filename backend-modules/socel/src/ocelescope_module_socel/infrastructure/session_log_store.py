from ocelescope import OCEL
from ocelescope_backend.app.internal.session import Session


class SessionLogStore:
    """The logs of the user's Ocelescope session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, ocel: OCEL, name: str) -> str:
        return self._session.add_ocel(ocel, name)
