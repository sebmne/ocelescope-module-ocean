"""Publication has one commit point, including when cleanup/notification fails."""

from collections.abc import Iterator
from copy import deepcopy
from pathlib import Path
from typing import Any

import pytest
from api import Api
from ocelescope import OCEL, EventTypeFilter
from ocelescope_backend.app.internal.exceptions import NotFound
from ocelescope_backend.app.internal.model.ocel import SessionOCEL
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_socel.application.ports.socel_workspace import SocelWork
from ocelescope_module_socel.domain.models.preparation import Preparation
from ocelescope_module_socel.infrastructure.adapters import ocelescope_log_store as store_module
from ocelescope_module_socel.infrastructure.adapters.ocelescope_socel_workspace import (
    OcelescopeSocelWorkspace,
)


@pytest.fixture
def prepared(session: Session, socel: str) -> Iterator[SocelWork]:
    with session.get_ocel(socel, use_original=True) as source:
        with OcelescopeSocelWorkspace(session, source, ocel_id=socel).open() as work:
            work.apply(Preparation(activities={"ship": None}), None)
            work.validate()
            yield work


def ship_class(api: Api, ocel_id: str) -> str | None:
    activities = api.get_log_classification(ocel_id, original=True).json()["activities"]
    return next(activity["socelClass"] for activity in activities if activity["name"] == "ship")


def fail_notification(*args: Any, **kwargs: Any) -> None:
    raise RuntimeError("notification failed")


def test_failed_new_log_write_removes_only_its_own_partial_file(
    monkeypatch: pytest.MonkeyPatch, prepared: SocelWork, api: Api, session: Session, socel: str
) -> None:
    directory = session.ocels[socel].db_path.parent
    before = set(directory.iterdir())
    handles = set(session.ocels)
    unrelated = directory / "another-operation.duckdb"

    def fail(self: OCEL, db_path: str | Path) -> None:
        Path(db_path).touch()
        unrelated.touch()
        raise RuntimeError("write failed")

    with monkeypatch.context() as patch:
        patch.setattr(OCEL, "to_duckdb", fail)
        with pytest.raises(RuntimeError, match="write failed"):
            prepared.publish_new("failed build")
    assert set(session.ocels) == handles
    assert set(directory.iterdir()) == before | {unrelated}
    assert ship_class(api, socel) == "op.logistics.transport"


def test_failed_registration_removes_the_completed_unregistered_file(
    monkeypatch: pytest.MonkeyPatch, prepared: SocelWork, session: Session, socel: str
) -> None:
    directory = session.ocels[socel].db_path.parent
    files = set(directory.iterdir())
    handles = set(session.ocels)

    def fail(*args: Any, **kwargs: Any) -> str:
        raise RuntimeError("registration failed")

    with monkeypatch.context() as patch:
        patch.setattr(Session, "_register_ocel", fail)
        with pytest.raises(RuntimeError, match="registration failed"):
            prepared.publish_new("failed registration")
    assert set(session.ocels) == handles
    assert set(directory.iterdir()) == files


def test_new_log_remains_successful_if_notification_fails_after_registration(
    monkeypatch: pytest.MonkeyPatch, prepared: SocelWork, api: Api, session: Session, socel: str
) -> None:
    before = set(session.ocels)
    with monkeypatch.context() as patch:
        patch.setattr(store_module.sse_manager, "send_safe", fail_notification)
        created = prepared.publish_new("committed build")
    assert set(session.ocels) == before | {created}
    assert session.ocels[created].name == "committed build"
    assert ship_class(api, created) is None
    assert ship_class(api, socel) == "op.logistics.transport"
    with pytest.raises(RuntimeError, match="already"):
        prepared.publish_new("must not duplicate")


def test_replacement_keeps_its_commit_if_old_file_removal_fails_and_retries_cleanup(
    monkeypatch: pytest.MonkeyPatch, prepared: SocelWork, api: Api, session: Session, socel: str
) -> None:
    previous = session.ocels[socel].db_path
    unlink = Path.unlink

    def fail(path: Path, *args: Any, **kwargs: Any) -> None:
        if path == previous:
            raise PermissionError("file temporarily locked")
        unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(Path, "unlink", fail)
        prepared.publish_replacing()
    assert session.ocels[socel].db_path != previous
    assert previous.exists()
    assert ship_class(api, socel) is None
    created = prepared_source_copy(session, socel)
    assert not previous.exists()
    assert session.ocels[created].db_path.exists()


def prepared_source_copy(session: Session, ocel_id: str) -> str:
    with session.get_ocel(ocel_id, use_original=True) as source, deepcopy(source) as copy:
        return store_module.OcelescopeLogStore(session).add(copy, "next publication")


def test_replacement_remains_successful_if_notification_fails_after_the_switch(
    monkeypatch: pytest.MonkeyPatch, prepared: SocelWork, api: Api, session: Session, socel: str
) -> None:
    previous = session.ocels[socel].db_path
    with monkeypatch.context() as patch:
        patch.setattr(store_module.sse_manager, "send_safe", fail_notification)
        prepared.publish_replacing()
    assert session.ocels[socel].db_path != previous
    assert not previous.exists()
    assert ship_class(api, socel) is None
    with pytest.raises(RuntimeError, match="already"):
        prepared.publish_replacing()


def test_a_reader_open_before_replacement_keeps_its_original_snapshot(
    prepared: SocelWork, api: Api, session: Session, socel: str
) -> None:
    with session.get_ocel(socel, use_original=True) as reader:
        query = "SELECT socel_class FROM events WHERE \"ocel:eid\" = 'e3'"
        assert reader.sql(query).fetchone() == ("op.logistics.transport",)
        prepared.publish_replacing()
        assert ship_class(api, socel) is None
        assert reader.sql(query).fetchone() == ("op.logistics.transport",)


def test_failed_filter_invalidation_preserves_the_original_and_its_cached_view(
    monkeypatch: pytest.MonkeyPatch, prepared: SocelWork, session: Session, socel: str
) -> None:
    session.set_filter(socel, "test", [EventTypeFilter(event_types=["ship"])])
    previous = session.ocels[socel].db_path
    files = set(previous.parent.iterdir())
    with session.get_ocel(socel) as filtered:
        counts = filtered.sql("SELECT count(*) FROM events").fetchone()

    def fail(self: SessionOCEL) -> None:
        raise RuntimeError("invalidation failed")

    with monkeypatch.context() as patch:
        patch.setattr(SessionOCEL, "_drop_filtered", fail)
        with pytest.raises(RuntimeError, match="invalidation failed"):
            prepared.publish_replacing()
    assert session.ocels[socel].db_path == previous
    assert set(previous.parent.iterdir()) == files
    with session.get_ocel(socel) as filtered:
        assert filtered.sql("SELECT count(*) FROM events").fetchone() == counts


def test_cleanup_failure_preserves_the_write_error_and_retries_only_the_owned_file(
    monkeypatch: pytest.MonkeyPatch, prepared: SocelWork, session: Session, socel: str
) -> None:
    partial: list[Path] = []
    unlink = Path.unlink

    def fail_write(self: OCEL, db_path: str | Path) -> None:
        path = Path(db_path)
        partial.append(path)
        path.touch()
        raise RuntimeError("original write error")

    def fail_cleanup(path: Path, *args: Any, **kwargs: Any) -> None:
        if path in partial:
            raise PermissionError("cleanup failed")
        unlink(path, *args, **kwargs)

    with monkeypatch.context() as patch:
        patch.setattr(OCEL, "to_duckdb", fail_write)
        patch.setattr(Path, "unlink", fail_cleanup)
        with pytest.raises(RuntimeError, match="original write error"):
            prepared.publish_new("failed")
    assert len(partial) == 1 and partial[0].exists()
    created = prepared_source_copy(session, socel)
    assert not partial[0].exists()
    assert session.ocels[created].db_path.exists()


def test_deletion_during_a_replacement_does_not_resurrect_the_handle_or_leave_a_file(
    monkeypatch: pytest.MonkeyPatch, prepared: SocelWork, session: Session, socel: str
) -> None:
    directory = session.ocels[socel].db_path.parent
    previous = session.ocels[socel].db_path
    before = set(directory.iterdir())
    write = OCEL.to_duckdb

    def delete_after_write(self: OCEL, db_path: str | Path) -> None:
        write(self, db_path)
        session.delete_ocel(socel)

    with monkeypatch.context() as patch:
        patch.setattr(OCEL, "to_duckdb", delete_after_write)
        with pytest.raises(NotFound):
            prepared.publish_replacing()
    assert socel not in session.ocels
    assert set(directory.iterdir()) == before - {previous}
