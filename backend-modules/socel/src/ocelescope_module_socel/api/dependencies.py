"""Composition root: the only place that knows which adapter implements which port."""

from threading import Lock
from typing import Annotated

from fastapi import Depends, HTTPException
from ocelescope import OCELExtensionError
from ocelescope_backend.app.dependencies import ApiOcel, ApiSession
from socel import SOCEL

from ocelescope_module_socel.application.ports.log_classifier import LogClassifier
from ocelescope_module_socel.application.ports.log_store import LogStore
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.application.use_cases.build_socel import BuildSocel
from ocelescope_module_socel.application.use_cases.get_class_counts import GetClassCounts
from ocelescope_module_socel.application.use_cases.get_class_taxonomies import (
    GetClassTaxonomies,
)
from ocelescope_module_socel.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
)
from ocelescope_module_socel.application.use_cases.get_log_classification import (
    GetLogClassification,
)
from ocelescope_module_socel.application.use_cases.get_socel_status import GetSocelStatus
from ocelescope_module_socel.application.use_cases.upload_record_file import UploadRecordFile
from ocelescope_module_socel.infrastructure.duckdb_log_classifier import DuckDbLogClassifier
from ocelescope_module_socel.infrastructure.duckdb_record_importer import DuckDbRecordImporter
from ocelescope_module_socel.infrastructure.duckdb_socel_statistics import DuckDbSocelStatistics
from ocelescope_module_socel.infrastructure.session_log_store import SessionLogStore
from ocelescope_module_socel.infrastructure.session_upload_store import SessionUploadStore

_VALIDATED = "socel:validated"


class _ValidatedLogs(set[str]):
    """The database files of a session's logs that passed the sOCEL check. A page
    asks for several things at once: the lock lets the first request check and
    the others wait for its result."""

    def __init__(self) -> None:
        super().__init__()
        self.lock = Lock()


def get_socel(ocel: ApiOcel, session: ApiSession) -> SOCEL:
    """The request's log as an sOCEL; a log that is none is answered with 422 and
    the reason before the use case is built.

    The check runs all conformance rules, which takes seconds on a large log, so
    a log is checked once and not on every request: a session's logs are files
    that are written once and never changed.
    """
    (path,) = ocel.sql(
        "SELECT path FROM duckdb_databases() WHERE database_name = current_database()"
    ).fetchall()[0]
    validated = session.get_module_state(_VALIDATED, _ValidatedLogs)
    with validated.lock:
        if path in validated:
            return SOCEL(ocel.con.cursor())
        try:
            socel = SOCEL.from_ocel(ocel)
        except OCELExtensionError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        validated.add(path)
        return socel


type ApiSocel = Annotated[SOCEL, Depends(get_socel)]


def get_socel_statistics() -> SocelStatistics:
    return DuckDbSocelStatistics()


def get_socel_status(
    statistics: Annotated[SocelStatistics, Depends(get_socel_statistics)],
) -> GetSocelStatus:
    return GetSocelStatus(statistics=statistics)


def get_flow_inventory(
    statistics: Annotated[SocelStatistics, Depends(get_socel_statistics)],
) -> GetFlowInventory:
    return GetFlowInventory(statistics=statistics)


def get_class_counts(
    statistics: Annotated[SocelStatistics, Depends(get_socel_statistics)],
) -> GetClassCounts:
    return GetClassCounts(statistics=statistics)


def get_log_classifier() -> LogClassifier:
    return DuckDbLogClassifier()


def get_log_store(session: ApiSession) -> LogStore:
    return SessionLogStore(session)


def get_record_importer() -> RecordImporter:
    return DuckDbRecordImporter()


def get_upload_store(session: ApiSession) -> UploadStore:
    return SessionUploadStore(session)


def get_class_taxonomies() -> GetClassTaxonomies:
    return GetClassTaxonomies()


def get_log_classification(
    classifier: Annotated[LogClassifier, Depends(get_log_classifier)],
) -> GetLogClassification:
    return GetLogClassification(classifier=classifier)


def get_upload_record_file(
    importer: Annotated[RecordImporter, Depends(get_record_importer)],
    uploads: Annotated[UploadStore, Depends(get_upload_store)],
) -> UploadRecordFile:
    return UploadRecordFile(importer=importer, uploads=uploads)


def get_build_socel(
    classifier: Annotated[LogClassifier, Depends(get_log_classifier)],
    importer: Annotated[RecordImporter, Depends(get_record_importer)],
    uploads: Annotated[UploadStore, Depends(get_upload_store)],
    store: Annotated[LogStore, Depends(get_log_store)],
) -> BuildSocel:
    return BuildSocel(classifier=classifier, importer=importer, uploads=uploads, store=store)
