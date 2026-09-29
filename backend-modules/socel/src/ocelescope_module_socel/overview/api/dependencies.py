"""Composition root: the only place that knows which adapter implements which port."""

from ocelescope_backend.app.dependencies import ApiOcel, ApiSession

from ocelescope_module_socel.overview.application.use_cases.export_socel import ExportSocel
from ocelescope_module_socel.overview.application.use_cases.get_class_counts import GetClassCounts
from ocelescope_module_socel.overview.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
)
from ocelescope_module_socel.overview.application.use_cases.get_socel_status import GetSocelStatus
from ocelescope_module_socel.overview.application.use_cases.validate_socel import ValidateSocel
from ocelescope_module_socel.overview.infrastructure.session_ocel_catalog import (
    SessionOcelCatalog,
)


def get_validate_socel(ocel: ApiOcel) -> ValidateSocel:
    return ValidateSocel(ocel=ocel)


def get_socel_status(session: ApiSession, ocel: ApiOcel) -> GetSocelStatus:
    return GetSocelStatus(ocel=ocel, catalog=SessionOcelCatalog(session))


def get_export_socel(session: ApiSession, ocel: ApiOcel) -> ExportSocel:
    return ExportSocel(ocel=ocel, catalog=SessionOcelCatalog(session))


def get_flow_inventory(ocel: ApiOcel) -> GetFlowInventory:
    return GetFlowInventory(ocel=ocel)


def get_class_counts(ocel: ApiOcel) -> GetClassCounts:
    return GetClassCounts(ocel=ocel)
