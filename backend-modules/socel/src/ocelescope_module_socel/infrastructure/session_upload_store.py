from uuid import uuid4

from ocelescope_backend.app.internal.session import Session

_STATE_KEY = "socel:uploads"


class _Uploads(dict[str, bytes]):
    """The uploads of one session, in memory."""


class SessionUploadStore:
    """Uploads kept with the user's Ocelescope session, gone when it ends. Only
    the latest one is kept: an upload replaces the one before."""

    def __init__(self, session: Session) -> None:
        self._uploads = session.get_module_state(_STATE_KEY, _Uploads)

    def put(self, content: bytes) -> str:
        upload_id = str(uuid4())
        self._uploads.clear()
        self._uploads[upload_id] = content
        return upload_id

    def get(self, upload_id: str) -> bytes | None:
        return self._uploads.get(upload_id)
