"""Failures after preparation, with real host logs and disposable DuckDB copies."""

from copy import deepcopy
from pathlib import Path
from typing import Any

import duckdb
import pytest
from api import Api
from ocelescope import OCEL
from ocelescope_backend.app.internal.session import Session

from ocelescope_module_socel.api.dependencies import get_socel
from ocelescope_module_socel.domain.models.preparation import Preparation
from ocelescope_module_socel.infrastructure.adapters import (
    ocelescope_socel_workspace as workspace_module,
)
from ocelescope_module_socel.infrastructure.adapters.duckdb_log_classifier import (
    DuckDbLogClassifier,
)
from ocelescope_module_socel.infrastructure.adapters.ocelescope_socel_workspace import (
    OcelescopeSocelWorkspace,
)


def test_a_write_failure_closes_the_copy_and_preserves_the_source(
    monkeypatch: pytest.MonkeyPatch, api: Api, session: Session, socel: str
) -> None:
    before = api.get_socel_status(socel).json()
    copies: list[OCEL] = []

    def clone(ocel: OCEL) -> OCEL:
        copy = deepcopy(ocel)
        copies.append(copy)
        return copy

    def fail(self: DuckDbLogClassifier, **kwargs: Any) -> None:
        raise RuntimeError("write failed")

    with session.get_ocel(socel, use_original=True) as source:
        with monkeypatch.context() as patch:
            patch.setattr(workspace_module, "deepcopy", clone)
            patch.setattr(DuckDbLogClassifier, "classify", fail)
            with pytest.raises(RuntimeError, match="write failed"):
                with OcelescopeSocelWorkspace(session, source, ocel_id=socel).open() as work:
                    work.apply(Preparation(), None)
        assert source.sql("SELECT 1").fetchone() == (1,)

    assert len(copies) == 1
    with pytest.raises(duckdb.ConnectionException):
        copies[0].sql("SELECT 1")
    assert api.get_socel_status(socel).json() == before


def test_failed_replacement_removes_partial_file_and_preserves_old_handle(
    monkeypatch: pytest.MonkeyPatch, api: Api, session: Session, socel: str
) -> None:
    before = api.get_socel_status(socel).json()
    previous = session.ocels[socel].db_path
    files = set(previous.parent.iterdir())

    def fail(self: OCEL, path: Path, **kwargs: Any) -> None:
        path.touch()
        raise RuntimeError("publication failed")

    with session.get_ocel(socel, use_original=True) as source:
        with OcelescopeSocelWorkspace(session, source, ocel_id=socel).open() as work:
            work.apply(Preparation(), None)
            work.validate()
            with monkeypatch.context() as patch:
                patch.setattr(OCEL, "to_duckdb", fail)
                with pytest.raises(RuntimeError, match="publication failed"):
                    work.publish_replacing()

    assert session.ocels[socel].db_path == previous
    assert set(previous.parent.iterdir()) == files
    assert api.get_socel_status(socel).json() == before


def test_publication_requires_conformance_validation(session: Session, socel: str) -> None:
    with session.get_ocel(socel, use_original=True) as source:
        with OcelescopeSocelWorkspace(session, source, ocel_id=socel).open() as work:
            work.apply(Preparation(), None)
            with pytest.raises(RuntimeError, match="Validate"):
                work.publish_replacing()


@pytest.mark.parametrize("cached", [False, True])
def test_extension_cursor_closes_without_closing_the_borrowed_log(
    session: Session, socel: str, cached: bool
) -> None:
    with session.get_ocel(socel, use_original=True) as source:
        if cached:
            first = get_socel(source, session)
            next(first)
            first.close()
        dependency = get_socel(source, session)
        extension = next(dependency)
        dependency.close()
        with pytest.raises(duckdb.ConnectionException):
            extension.sql("SELECT 1")
        assert source.sql("SELECT 1").fetchone() == (1,)
