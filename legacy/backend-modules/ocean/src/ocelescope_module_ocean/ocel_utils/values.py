"""Reading values out of an Ocelescope OCEL, as collected polars frames.

Independent of OCEAn (enforced by import-linter): useful for any OCEL analysis.
"""

import polars as pl
from ocelescope import OCEL

EID, OID = "ocel:eid", "ocel:oid"
ACTIVITY, OBJECT_TYPE = "ocel:activity", "ocel:type"
QUALIFIER, TIMESTAMP = "ocel:qualifier", "ocel:timestamp"

# One time unit for every timestamp we compare (the OCEL's tables may differ).
_TIME = pl.Datetime("us")


def events_of(ocel: OCEL, activity: str, attributes: list[str]) -> pl.DataFrame:
    """The activity's events with their timestamp and the given event attributes."""
    return (
        ocel.events.pl.filter(pl.col(ACTIVITY) == activity)
        .select(EID, pl.col(TIMESTAMP).cast(_TIME), *attributes)
        .collect()
    )


def relations_of(
    ocel: OCEL, activity: str, object_type: str, qualifier: str | None = None
) -> pl.DataFrame:
    """E2O relations from the activity's events to objects of the type."""
    relations = ocel.e2o.pl.filter(
        (pl.col(ACTIVITY) == activity) & (pl.col(OBJECT_TYPE) == object_type)
    )
    if qualifier is not None:
        relations = relations.filter(pl.col(QUALIFIER) == qualifier)
    return relations.select(EID, OID, pl.col(TIMESTAMP).cast(_TIME)).collect()


def object_values_at_events(
    ocel: OCEL, relations: pl.DataFrame, object_type: str, attributes: list[str]
) -> pl.DataFrame:
    """Each relation with the values its object's attributes had at the event's time.

    A change at the same timestamp as the event already counts, like in the
    original OCEAn. Initial values are stored at the epoch, so they always apply.
    """
    states = (
        ocel.objects.attribute_states(object_types=[object_type], attributes=attributes)
        .pl()
        .with_columns(pl.col(TIMESTAMP).cast(_TIME))
        .sort(TIMESTAMP)
    )
    return relations.sort(TIMESTAMP).join_asof(
        states.select(OID, TIMESTAMP, *attributes),
        on=TIMESTAMP,
        by=OID,
        strategy="backward",
        # Sorted by timestamp overall, hence within each object; polars cannot
        # verify that for grouped joins and would warn.
        check_sortedness=False,
    )
