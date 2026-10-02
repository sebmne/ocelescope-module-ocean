"""Composition root: the only place that knows which adapter implements which port."""

from typing import Annotated

from fastapi import Depends
from ocelescope_backend.app.dependencies import get_ocel_extension
from socel import SOCEL

from ocelescope_module_socel.application.use_cases.get_class_counts import GetClassCounts
from ocelescope_module_socel.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
)
from ocelescope_module_socel.application.use_cases.get_socel_status import GetSocelStatus

# The request's log as a validated sOCEL; a log that is none is rejected with 422
# before the use case is built.
ApiSocel = Annotated[SOCEL, Depends(get_ocel_extension(SOCEL))]


def get_socel_status(socel: ApiSocel) -> GetSocelStatus:
    return GetSocelStatus(socel=socel)


def get_flow_inventory(socel: ApiSocel) -> GetFlowInventory:
    return GetFlowInventory(socel=socel)


def get_class_counts(socel: ApiSocel) -> GetClassCounts:
    return GetClassCounts(socel=socel)
