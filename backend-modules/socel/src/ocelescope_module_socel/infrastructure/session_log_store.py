from uuid import uuid4

from ocelescope import OCEL
from ocelescope_backend.app.internal.exceptions import NotFound
from ocelescope_backend.app.internal.session import Session
from ocelescope_backend.app.sse_manager import InvalidationRequest, sse_manager


class SessionLogStore:
    """The logs of the user's Ocelescope session."""

    def __init__(self, session: Session) -> None:
        self._session = session

    def add(self, ocel: OCEL, name: str) -> str:
        return self._session.add_ocel(ocel, name)

    def get(self, ocel_id: str) -> OCEL:
        return self._session.get_ocel(ocel_id, use_original=True)

    def replace(self, ocel_id: str, ocel: OCEL) -> None:
        # The session has no call for this: its handle names the DuckDB file the
        # log lives in, so the new log is written beside it and the handle moved
        # over. Requests still reading the old file keep it open until they end.
        handle = self._session.ocels.get(ocel_id)
        if handle is None:
            raise NotFound(f"OCEL with id {ocel_id} not found")
        previous = handle.db_path
        path = previous.with_name(f"{ocel_id}.{uuid4().hex}.duckdb")
        ocel.to_duckdb(path)
        handle.db_path = path
        # The filtered copy was made from the old file; it is made again on the
        # next read.
        handle._drop_filtered()  # pyright: ignore[reportPrivateUsage]
        previous.unlink(missing_ok=True)
        sse_manager.send_safe(self._session.id, InvalidationRequest(routes=["ocels"]))
