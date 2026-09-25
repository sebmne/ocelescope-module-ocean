from dataclasses import dataclass

import polars as pl

EMISSIONS_KG = "ocean:emissions_kg"


# eq=False: the frames cannot be compared with ==, so neither can the object.
@dataclass(frozen=True, kw_only=True, eq=False)
class ProcessEmissions:
    """Emissions computed for one OCEL.

    Frames are collected (never lazy): the OCEL they were computed from is closed
    once the request ends, while these results outlive it.
    """

    # One row per event: ocel:eid, EMISSIONS_KG
    event_emissions: pl.DataFrame
    # One row per event-to-object relation: ocel:eid, ocel:oid, EMISSIONS_KG
    e2o_emissions: pl.DataFrame
    # Sum of both frames; missing emissions count as nothing.
    total_kg: float


@dataclass(frozen=True, kw_only=True)
class EmissionsOverview:
    """Totals in kg CO2e; None where nothing was computed yet."""

    rule_based_kg: float | None
    imported_kg: float | None
    total_kg: float | None
