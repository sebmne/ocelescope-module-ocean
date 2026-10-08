"""Composition root: the only place that knows which adapter implements which port."""

from typing import Annotated

from fastapi import Depends
from ocelescope_backend.app.dependencies import ApiSession, ocel_as
from socel import SOCEL

from ocelescope_module_socel.application.ports.log_classifier import LogClassifier
from ocelescope_module_socel.application.ports.log_store import LogStore
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
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
from ocelescope_module_socel.infrastructure.session_log_store import SessionLogStore
from ocelescope_module_socel.infrastructure.session_upload_store import SessionUploadStore

type ApiSocel = Annotated[SOCEL, Depends(ocel_as(SOCEL))]


def get_socel_status() -> GetSocelStatus:
    return GetSocelStatus()


def get_flow_inventory() -> GetFlowInventory:
    return GetFlowInventory()


def get_class_counts() -> GetClassCounts:
    return GetClassCounts()


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
