"""A flow's unit in the terms of Climatiq's estimate parameters."""

from dataclasses import dataclass


@dataclass(frozen=True)
class ClimatiqUnit:
    unit_type: str
    # The parameter the amount goes in, and the one its unit goes in; Number
    # has no unit.
    amount: str
    unit_parameter: str | None
    unit: str | None

    def parameters(self, amount: float) -> dict[str, float | str]:
        """Estimate parameters for `amount` of this unit."""
        parameters: dict[str, float | str] = {self.amount: amount}
        if self.unit_parameter is not None and self.unit is not None:
            parameters[self.unit_parameter] = self.unit
        return parameters


def _simple(unit_type: str, parameter: str, *units: str) -> dict[str, ClimatiqUnit]:
    return {
        unit.lower(): ClimatiqUnit(unit_type, parameter, f"{parameter}_unit", unit)
        for unit in units
    }


# Climatiq's units of single-quantity unit types, by lowercase name; its
# compound types (e.g. weight over distance) are no unit of a flow.
_UNITS: dict[str, ClimatiqUnit] = {
    **_simple("Energy", "energy", "Wh", "kWh", "MWh", "GWh", "MJ", "GJ", "TJ", "therm", "MMBTU"),
    **_simple("Weight", "weight", "g", "kg", "t", "lb", "ton"),
    **_simple("Volume", "volume", "ml", "l", "m3", "cubic_foot", "gallon_us", "bbl"),
    **_simple("Distance", "distance", "m", "km", "ft", "mi", "nmi"),
    **_simple("Area", "area", "m2", "km2", "ft2", "ha"),
    **_simple("Time", "time", "ms", "s", "min", "hour", "day", "year"),
    **_simple("Power", "power", "W", "kW", "MW"),
    **_simple("Data", "data", "MB", "GB", "TB"),
}

# Other spellings of the same units, as flows are written (pint style, e.g.
# "m**3", or words).
_ALIASES = {
    "tonne": "t",
    "tonnes": "t",
    "liter": "l",
    "litre": "l",
    "liters": "l",
    "litres": "l",
    "h": "hour",
    "hours": "hour",
    "days": "day",
    "years": "year",
}

_NUMBER = ClimatiqUnit("Number", "number", None, None)
_COUNTS = {"pcs", "pc", "piece", "pieces", "unit", "units", "item", "items", "number"}


def climatiq_unit(unit: str) -> ClimatiqUnit | None:
    """The Climatiq unit a flow's unit is, None for one Climatiq does not know."""
    name = unit.strip().replace("**", "").replace("^", "").replace("³", "3").replace("²", "2")
    name = name.lower()
    if name in _COUNTS:
        return _NUMBER
    return _UNITS.get(_ALIASES.get(name, name))
