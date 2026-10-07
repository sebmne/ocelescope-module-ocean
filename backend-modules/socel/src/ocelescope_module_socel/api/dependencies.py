"""Composition root: the only place that knows which adapter implements which port."""

from typing import Annotated

from fastapi import Depends
from ocelescope_backend.app.dependencies import ocel_as
from socel import SOCEL

from ocelescope_module_socel.application.use_cases.get_class_counts import GetClassCounts
from ocelescope_module_socel.application.use_cases.get_flow_inventory import (
    GetFlowInventory,
)
from ocelescope_module_socel.application.use_cases.get_socel_status import GetSocelStatus

type ApiSocel = Annotated[SOCEL, Depends(ocel_as(SOCEL))]


def get_socel_status() -> GetSocelStatus:
    return GetSocelStatus()


def get_flow_inventory() -> GetFlowInventory:
    return GetFlowInventory()


def get_class_counts() -> GetClassCounts:
    return GetClassCounts()
