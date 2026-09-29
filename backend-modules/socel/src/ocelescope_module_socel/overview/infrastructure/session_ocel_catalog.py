from ocelescope_backend.app.internal.session import Session


class SessionOcelCatalog:
    """The OCELs of the user's session (implements OcelCatalog)."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def name(self, ocel_id: str) -> str:
        return self._session.ocels[ocel_id].name
