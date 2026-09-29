"""Composition root: the only place that knows which adapter implements which port."""

from ocelescope_backend.app.dependencies import ApiOcel, ApiSession

from ocelescope_module_socel.analysis.application.use_cases.get_allocation import GetAllocation
from ocelescope_module_socel.analysis.application.use_cases.get_analysis_settings import (
    GetAnalysisSettings,
)
from ocelescope_module_socel.analysis.application.use_cases.get_attribution import GetAttribution
from ocelescope_module_socel.analysis.application.use_cases.get_flow_series import GetFlowSeries
from ocelescope_module_socel.analysis.application.use_cases.get_impact import GetImpact
from ocelescope_module_socel.analysis.application.use_cases.save_analysis_settings import (
    SaveAnalysisSettings,
)
from ocelescope_module_socel.analysis.infrastructure.session_settings_repository import (
    SessionSettingsRepository,
)


def get_analysis_settings(session: ApiSession, ocel: ApiOcel) -> GetAnalysisSettings:
    return GetAnalysisSettings(ocel=ocel, settings=SessionSettingsRepository(session))


def get_save_analysis_settings(session: ApiSession) -> SaveAnalysisSettings:
    return SaveAnalysisSettings(settings=SessionSettingsRepository(session))


def get_flow_series(ocel: ApiOcel) -> GetFlowSeries:
    return GetFlowSeries(ocel=ocel)


def get_attribution(session: ApiSession, ocel: ApiOcel) -> GetAttribution:
    return GetAttribution(ocel=ocel, settings=SessionSettingsRepository(session))


def get_allocation(session: ApiSession, ocel: ApiOcel) -> GetAllocation:
    return GetAllocation(ocel=ocel, settings=SessionSettingsRepository(session))


def get_impact(session: ApiSession, ocel: ApiOcel) -> GetImpact:
    return GetImpact(ocel=ocel, settings=SessionSettingsRepository(session))
