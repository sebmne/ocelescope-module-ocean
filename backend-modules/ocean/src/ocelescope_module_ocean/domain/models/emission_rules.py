from dataclasses import dataclass

from ocelescope_module_ocean.domain.models.emission_factor import EmissionFactor


@dataclass(frozen=True, kw_only=True)
class EventEmissionRule:
    """Every event of the activity emits the factor's value, times its attributes."""

    activity: str
    factor: EmissionFactor


@dataclass(frozen=True, kw_only=True)
class E2OEmissionRule:
    """Every relation from an event of the activity to an object of the type emits.

    Besides event attributes and attributes of uniquely related objects, the
    factor can use the attributes of the relation's own object - which, unlike
    for event rules, need not be the only object of its type at the event.
    """

    activity: str
    object_type: str
    factor: EmissionFactor
    # Only relations with this qualifier; None means any.
    qualifier: str | None = None


EmissionRule = EventEmissionRule | E2OEmissionRule
