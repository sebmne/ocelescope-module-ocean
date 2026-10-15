import logging
from pathlib import Path
from threading import RLock
from uuid import uuid4

from ocelescope import OCEL
from ocelescope_backend.app.internal.exceptions import NotFound
from ocelescope_backend.app.internal.session import Session
from ocelescope_backend.app.sse_manager import InvalidationRequest, sse_manager

_LOGGER = logging.getLogger(__name__)
_PUBLICATION_STATE = "socel:publication"


class _PublicationState:
    def __init__(self) -> None:
        self.lock = RLock()
        self.retired: set[Path] = set()


class _PendingLog(OCEL):
    """Track this public Session.add_ocel call's target without copying its data.

    The host chooses the UUID/path. A borrowed cursor lets us observe the write
    and clean up that exact target if writing or registration fails.
    """

    target: Path | None = None

    def to_duckdb(self, db_path: str | Path) -> None:
        self.target = Path(db_path)
        super().to_duckdb(db_path)


class OcelescopeLogStore:
    """Publish through the host registry, with cleanup scoped to owned files."""

    def __init__(self, session: Session) -> None:
        self._session = session
        self._state = session.get_module_state(_PUBLICATION_STATE, _PublicationState)

    def add(self, ocel: OCEL, name: str) -> str:
        with self._state.lock:
            self._retry_cleanup()
            with _PendingLog(ocel.con.cursor()) as pending:
                try:
                    return self._session.add_ocel(pending, name)
                except BaseException as error:
                    committed = self._registered_id(pending.target)
                    if committed is None:
                        if pending.target is not None:
                            self._retire(pending.target)
                        raise
                    # At the pinned host version, registry insertion precedes
                    # notification. A notification failure cannot undo that commit.
                    if isinstance(error, Exception):
                        _LOGGER.warning(
                            "Log %s was committed but host notification failed.",
                            committed,
                            exc_info=True,
                        )
                        return committed
                    raise

    def replace(self, ocel_id: str, ocel: OCEL) -> None:
        with self._state.lock:
            self._retry_cleanup()
            handle = self._session.ocels.get(ocel_id)
            if handle is None:
                raise NotFound(f"OCEL with id {ocel_id} not found")
            previous = handle.db_path
            path = previous.with_name(f"{ocel_id}.{uuid4().hex}.duckdb")
            try:
                ocel.to_duckdb(path)
                if self._session.ocels.get(ocel_id) is not handle:
                    raise NotFound(f"OCEL with id {ocel_id} no longer exists")
                if handle.db_path != previous:
                    raise RuntimeError("The host log changed during publication.")
                # The host currently exposes no public replacement operation.
                # Finish fallible view invalidation before the handle switch.
                handle._drop_filtered()  # pyright: ignore[reportPrivateUsage]
            except BaseException:
                self._retire(path)
                raise

            # Commit point: readers now resolve the complete new database.
            handle.db_path = path
            self._retire(previous)
            try:
                sse_manager.send_safe(self._session.id, InvalidationRequest(routes=["ocels"]))
            except Exception:
                _LOGGER.warning(
                    "Log %s was committed but host notification failed.", ocel_id, exc_info=True
                )

    def _registered_id(self, path: Path | None) -> str | None:
        if path is None:
            return None
        return next(
            (
                ocel_id
                for ocel_id, handle in tuple(self._session.ocels.items())
                if handle.db_path == path
            ),
            None,
        )

    def _retire(self, path: Path) -> None:
        if self._registered_id(path) is not None:
            return
        try:
            path.unlink(missing_ok=True)
        except OSError:
            self._state.retired.add(path)
            _LOGGER.warning(
                "Could not remove unused log file %s; cleanup deferred.", path, exc_info=True
            )
        else:
            self._state.retired.discard(path)

    def _retry_cleanup(self) -> None:
        for path in tuple(self._state.retired):
            self._retire(path)
