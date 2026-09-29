from dataclasses import dataclass


@dataclass(frozen=True, kw_only=True)
class EmissionFactor:
    """The impact of one unit of a flow, in kg CO2e."""

    flow_id: str
    impact_per_unit: float


@dataclass(frozen=True, kw_only=True)
class AnalysisSettings:
    """What the analyst decides.

    group_metering: a meter whose nested meters record nothing also reaches the
        operations of the objects directly within it, as a line meter stands for
        its machines.
    created_from_qualifier: the O2O qualifier by which a handling unit is created
        from another; None: nothing is carried along a lineage.
    mass_attribute: the handling units' mass, by which a parent's quantities are
        split among its children.
    emission_factors: the flows with an impact; the others have none.
    """

    group_metering: bool = True
    created_from_qualifier: str | None = None
    mass_attribute: str | None = None
    emission_factors: tuple[EmissionFactor, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Choice:
    """A value a setting can take, and how much of the log it covers."""

    name: str
    count: int


@dataclass(frozen=True, kw_only=True)
class SettingsChoices:
    """What the log offers for the lineage settings: O2O qualifiers between
    handling units (count: relations), numeric unit attributes (count: units)."""

    created_from_qualifiers: tuple[Choice, ...]
    mass_attributes: tuple[Choice, ...]
