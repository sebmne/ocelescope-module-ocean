"""Composition root: the only place that knows which adapter implements which port."""

from collections.abc import Generator, Iterator
from functools import cache
from threading import Lock
from typing import Annotated

from fastapi import Depends, HTTPException
from ocelescope import OCEL, OCELExtensionError
from ocelescope_backend.app.dependencies import ApiOcel, ApiSession

from ocelescope_module_socel.application.ports.catalog_credentials import CatalogCredentials
from ocelescope_module_socel.application.ports.factor_catalog import FactorCatalogFactory
from ocelescope_module_socel.application.ports.log_classifier import LogClassifier
from ocelescope_module_socel.application.ports.record_importer import RecordImporter
from ocelescope_module_socel.application.ports.socel_statistics import SocelStatistics
from ocelescope_module_socel.application.ports.upload_store import UploadStore
from ocelescope_module_socel.application.use_cases.build_socel import BuildSocel
from ocelescope_module_socel.application.use_cases.calculate_impact import CalculateImpact
from ocelescope_module_socel.application.use_cases.configure_socel import ConfigureSocel
from ocelescope_module_socel.application.use_cases.connect_factor_catalog import (
    ConnectFactorCatalog,
)
from ocelescope_module_socel.application.use_cases.disconnect_factor_catalog import (
    DisconnectFactorCatalog,
)
from ocelescope_module_socel.application.use_cases.get_class_counts import GetClassCounts
from ocelescope_module_socel.application.use_cases.get_class_taxonomies import (
    GetClassTaxonomies,
)
from ocelescope_module_socel.application.use_cases.get_flow_instances import GetFlowInstances
from ocelescope_module_socel.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
)
from ocelescope_module_socel.application.use_cases.get_flow_records import GetFlowRecords
from ocelescope_module_socel.application.use_cases.get_log_classification import (
    GetLogClassification,
)
from ocelescope_module_socel.application.use_cases.get_socel_status import GetSocelStatus
from ocelescope_module_socel.application.use_cases.list_factor_catalogs import (
    ListFactorCatalogs,
)
from ocelescope_module_socel.application.use_cases.preview_record_file import PreviewRecordFile
from ocelescope_module_socel.application.use_cases.resolve_catalog_factor import (
    ResolveCatalogFactor,
)
from ocelescope_module_socel.application.use_cases.search_factor_catalog import (
    SearchFactorCatalog,
)
from ocelescope_module_socel.application.use_cases.upload_record_file import UploadRecordFile
from ocelescope_module_socel.application.workflows.apply_socel_changes import ApplySocelChanges
from ocelescope_module_socel.application.workflows.open_factor_catalog import OpenFactorCatalog
from ocelescope_module_socel.domain.services.impact_calculator import ImpactCalculator
from ocelescope_module_socel.domain.services.preparation_validator import PreparationValidator
from ocelescope_module_socel.infrastructure.adapters.duckdb_flow_analysis import DuckDbFlowAnalysis
from ocelescope_module_socel.infrastructure.adapters.duckdb_log_classifier import (
    DuckDbLogClassifier,
)
from ocelescope_module_socel.infrastructure.adapters.duckdb_record_importer import (
    DuckDbRecordImporter,
)
from ocelescope_module_socel.infrastructure.adapters.duckdb_socel_statistics import (
    DuckDbSocelStatistics,
)
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.climatiq import (
    ClimatiqConnector,
)
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.factory import (
    ExternalFactorCatalogFactory,
)
from ocelescope_module_socel.infrastructure.adapters.factor_catalogs.file_credentials import (
    FileCatalogCredentials,
)
from ocelescope_module_socel.infrastructure.adapters.ocelescope_socel_workspace import (
    OcelescopeSocelWorkspace,
)
from ocelescope_module_socel.infrastructure.adapters.ocelescope_upload_store import (
    OcelescopeUploadStore,
)
from ocelescope_module_socel.infrastructure.ocelescope_extension import SOCEL
from ocelescope_module_socel.infrastructure.settings import SocelSettings

_VALIDATED = "socel:validated"


class _ValidatedLogs(set[str]):
    """The database files of a session's logs that passed the sOCEL check. A page
    asks for several things at once: the lock lets the first request check and
    the others wait for its result."""

    def __init__(self) -> None:
        super().__init__()
        self.lock = Lock()


def get_socel(ocel: ApiOcel, session: ApiSession) -> Generator[SOCEL]:
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
            socel = SOCEL(ocel.con.cursor())
        else:
            try:
                socel = SOCEL.from_ocel(ocel)
            except OCELExtensionError as error:
                raise HTTPException(status_code=422, detail=str(error)) from error
            validated.add(path)
    try:
        yield socel
    finally:
        socel.close()


type ApiSocel = Annotated[SOCEL, Depends(get_socel)]


def get_socel_statistics(socel: ApiSocel) -> SocelStatistics:
    return DuckDbSocelStatistics(socel)


def get_socel_status(
    statistics: Annotated[SocelStatistics, Depends(get_socel_statistics)],
) -> GetSocelStatus:
    return GetSocelStatus(statistics=statistics)


def get_flow_inventory(
    statistics: Annotated[SocelStatistics, Depends(get_socel_statistics)],
) -> GetFlowInventory:
    return GetFlowInventory(statistics=statistics)


def get_flow_instances(
    statistics: Annotated[SocelStatistics, Depends(get_socel_statistics)],
) -> GetFlowInstances:
    return GetFlowInstances(statistics=statistics)


def get_flow_records(
    statistics: Annotated[SocelStatistics, Depends(get_socel_statistics)],
) -> GetFlowRecords:
    return GetFlowRecords(statistics=statistics)


def get_calculate_impact(socel: ApiSocel) -> CalculateImpact:
    return CalculateImpact(flows=DuckDbFlowAnalysis(socel), calculator=ImpactCalculator())


def get_class_counts(
    statistics: Annotated[SocelStatistics, Depends(get_socel_statistics)],
) -> GetClassCounts:
    return GetClassCounts(statistics=statistics)


def get_log_classifier(ocel: ApiOcel) -> LogClassifier:
    return DuckDbLogClassifier(ocel)


def get_record_importer(ocel: ApiOcel) -> RecordImporter:
    return DuckDbRecordImporter(ocel)


def get_upload_store(session: ApiSession) -> UploadStore:
    return OcelescopeUploadStore(session)


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


def get_preview_record_file(
    importer: Annotated[RecordImporter, Depends(get_record_importer)],
    uploads: Annotated[UploadStore, Depends(get_upload_store)],
) -> PreviewRecordFile:
    return PreviewRecordFile(importer=importer, uploads=uploads)


def get_apply_socel_changes(
    uploads: Annotated[UploadStore, Depends(get_upload_store)],
) -> ApplySocelChanges:
    return ApplySocelChanges(uploads=uploads, validator=PreparationValidator())


def get_original_ocel(ocel_id: str, session: ApiSession) -> Iterator[OCEL]:
    with session.get_ocel(ocel_id, use_original=True) as ocel:
        yield ocel


type ApiOriginalOcel = Annotated[OCEL, Depends(get_original_ocel)]


def get_configure_socel(
    ocel_id: str,
    ocel: ApiOriginalOcel,
    session: ApiSession,
    apply: Annotated[ApplySocelChanges, Depends(get_apply_socel_changes)],
) -> ConfigureSocel:
    return ConfigureSocel(
        apply=apply, workspace=OcelescopeSocelWorkspace(session, ocel, ocel_id=ocel_id)
    )


def get_build_socel(
    ocel: ApiOcel,
    session: ApiSession,
    apply: Annotated[ApplySocelChanges, Depends(get_apply_socel_changes)],
) -> BuildSocel:
    return BuildSocel(apply=apply, workspace=OcelescopeSocelWorkspace(session, ocel))


@cache
def get_settings() -> SocelSettings:
    """The module's configuration, read once."""
    return SocelSettings()


type ApiSettings = Annotated[SocelSettings, Depends(get_settings)]


def get_catalog_credentials(settings: ApiSettings) -> CatalogCredentials:
    key = settings.climatiq_api_key
    return FileCatalogCredentials(
        settings.module_dir / "factor_catalogs.json",
        environment={"climatiq": key.get_secret_value() if key is not None else None},
    )


def get_factor_catalog_factory(settings: ApiSettings) -> FactorCatalogFactory:
    return _factor_catalog_factory(settings.climatiq_data_version)


@cache
def _factor_catalog_factory(climatiq_data_version: str | None) -> ExternalFactorCatalogFactory:
    # The catalogs on offer, in the order they are shown; each knows its own id,
    # name and website. One factory per configuration: the catalogs its
    # providers opened serve the next requests.
    return ExternalFactorCatalogFactory(
        [ClimatiqConnector(data_version=climatiq_data_version)],
    )


type ApiFactorCatalogFactory = Annotated[FactorCatalogFactory, Depends(get_factor_catalog_factory)]
type ApiCatalogCredentials = Annotated[CatalogCredentials, Depends(get_catalog_credentials)]


def get_list_factor_catalogs(
    factory: ApiFactorCatalogFactory, credentials: ApiCatalogCredentials
) -> ListFactorCatalogs:
    return ListFactorCatalogs(factory=factory, credentials=credentials)


def get_connect_factor_catalog(
    factory: ApiFactorCatalogFactory, credentials: ApiCatalogCredentials
) -> ConnectFactorCatalog:
    return ConnectFactorCatalog(factory=factory, credentials=credentials)


def get_disconnect_factor_catalog(
    factory: ApiFactorCatalogFactory, credentials: ApiCatalogCredentials
) -> DisconnectFactorCatalog:
    return DisconnectFactorCatalog(factory=factory, credentials=credentials)


def get_open_factor_catalog(
    factory: ApiFactorCatalogFactory, credentials: ApiCatalogCredentials
) -> OpenFactorCatalog:
    return OpenFactorCatalog(factory=factory, credentials=credentials)


type ApiOpenFactorCatalog = Annotated[OpenFactorCatalog, Depends(get_open_factor_catalog)]


def get_search_factor_catalog(open_catalog: ApiOpenFactorCatalog) -> SearchFactorCatalog:
    return SearchFactorCatalog(open_catalog=open_catalog)


def get_resolve_catalog_factor(open_catalog: ApiOpenFactorCatalog) -> ResolveCatalogFactor:
    return ResolveCatalogFactor(open_catalog=open_catalog)
