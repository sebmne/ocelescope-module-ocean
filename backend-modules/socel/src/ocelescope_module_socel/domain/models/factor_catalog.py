from typing import Literal

from pydantic import FiniteFloat

from ocelescope_module_socel.domain.models.base import Model

# Where the catalog's API key comes from: set for the installation in its
# environment, or saved from the app.
type KeySource = Literal["environment", "saved"]


class FactorCatalogInfo(Model):
    """An external database of emission factors the module can consult: its id,
    name and website, whether it can be consulted, and where its key comes from
    (None: there is none)."""

    id: str
    name: str
    website: str
    available: bool
    key: KeySource | None


class FactorQuery(Model):
    """What to look for in a factor catalog.

    `unit` keeps the factors that can be expressed per that unit, e.g. a
    flow's "kWh"; `region` and `year` narrow the factors to where and when
    they hold, in the catalog's own terms.
    """

    text: str
    unit: str | None = None
    region: str | None = None
    year: int | None = None


class CatalogFactor(Model):
    """An emission factor as the catalog lists it: `value` kg CO2e per `unit`.
    A catalog may list a factor without its value (Climatiq, without the
    add-on); resolving it still gives the value.

    `ref` is the catalog's own reference to it, opaque to the module, and is
    what a factor is resolved by later.
    """

    ref: str
    name: str
    source: str
    region: str | None
    year: int | None
    unit: str
    value: FiniteFloat | None


class ResolvedFactor(Model):
    """A catalog factor expressed per one unit of a flow: `value` kg CO2e per
    `unit`, with the factor it comes from."""

    unit: str
    value: FiniteFloat
    factor: CatalogFactor
