"""Follows the recorded flows from the meters to the operations they were recorded
during (attribution), on to the handling units of those operations (allocation)
and, with a lineage, down to the units created from them (carrying). Every use
case past attribution starts here."""

from dataclasses import dataclass

import polars as pl
from ocelescope import OCEL
from socel import (
    SOCEL,
    Allocation,
    Attribution,
    LineageError,
    allocate,
    attribute,
    carry,
    creation_values,
    parents,
)

from ocelescope_module_socel.analysis.domain.exceptions import NotAnSocelError
from ocelescope_module_socel.analysis.domain.models.analysis_settings import AnalysisSettings


@dataclass(frozen=True, eq=False)
class FlowTrace:
    socel: SOCEL
    attribution: Attribution
    allocation: Allocation
    # Which unit was created from which (object_id, parent_object_id), with a lineage.
    parent: pl.DataFrame | None
    # What every unit carries (flow_id, object_id, quantity, is_end), with a lineage.
    carried: pl.DataFrame | None
    # Masses at creation (object_id, value), with a mass attribute.
    masses: pl.DataFrame | None
    lineage_problem: str | None


def trace_flows(ocel: OCEL, ocel_id: str, settings: AnalysisSettings) -> FlowTrace:
    """Raises:
    NotAnSocelError: The OCEL has no sOCEL tables.
    """
    if not SOCEL.is_socel(ocel):
        raise NotAnSocelError(f"OCEL {ocel_id} has no sOCEL tables.")
    socel = SOCEL(ocel)
    attribution = attribute(socel, group_metering=settings.group_metering)
    allocation = allocate(socel, attribution)

    masses = parent = carried = None
    problem = None
    try:
        if settings.mass_attribute:
            masses = creation_values(socel, settings.mass_attribute)
        if settings.created_from_qualifier and masses is not None:
            parent = parents(socel, settings.created_from_qualifier)
            carried = carry(allocation.by_unit, parent, masses)
    except (LineageError, ValueError) as error:
        problem = str(error)
    return FlowTrace(
        socel=socel,
        attribution=attribution,
        allocation=allocation,
        parent=parent,
        carried=carried,
        masses=masses,
        lineage_problem=problem,
    )
