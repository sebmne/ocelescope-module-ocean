from dataclasses import dataclass

from ocelescope_module_ocean.domain.models.attributes import AttributeRef


@dataclass(frozen=True, kw_only=True)
class EmissionFactor:
    """A constant emission value, multiplied by the values of the attributes.

    Without attributes, `value_kg` is emitted once per event (or relation).
    """

    # kg CO2e per event, or per unit of the attributes. Units come with the
    # configuration page; until then everything is kg CO2e.
    value_kg: float
    attributes: tuple[AttributeRef, ...] = ()
