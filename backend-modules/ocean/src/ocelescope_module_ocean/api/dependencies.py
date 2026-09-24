"""Composition root: the only place that knows which adapter implements which port.

Every use case is built per request, from that request's session (and OCEL).
"""

from ocelescope_backend.app.dependencies import ApiOcel, ApiSession

from ocelescope_module_ocean.application.use_cases.allocate_emissions import AllocateEmissions
from ocelescope_module_ocean.application.use_cases.compute_emissions import ComputeEmissions
from ocelescope_module_ocean.application.use_cases.get_emissions_overview import (
    GetEmissionsOverview,
)
from ocelescope_module_ocean.application.use_cases.get_object_emissions import GetObjectEmissions
from ocelescope_module_ocean.infrastructure.session_emissions_repository import (
    SessionEmissionsRepository,
)


def get_emissions_overview(session: ApiSession) -> GetEmissionsOverview:
    return GetEmissionsOverview(emissions_repository=SessionEmissionsRepository(session))


def get_compute_emissions(session: ApiSession, ocel: ApiOcel) -> ComputeEmissions:
    return ComputeEmissions(ocel=ocel, emissions_repository=SessionEmissionsRepository(session))


def get_allocate_emissions(session: ApiSession, ocel: ApiOcel) -> AllocateEmissions:
    return AllocateEmissions(ocel=ocel, emissions_repository=SessionEmissionsRepository(session))


def get_object_emissions(session: ApiSession) -> GetObjectEmissions:
    return GetObjectEmissions(emissions_repository=SessionEmissionsRepository(session))
