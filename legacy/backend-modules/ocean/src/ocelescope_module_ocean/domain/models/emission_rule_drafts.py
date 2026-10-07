from dataclasses import dataclass
from typing import Literal

from ocelescope_module_ocean.domain.models.attributes import AttributeRef

EmissionRuleDraftType = Literal["event", "e2o"]


@dataclass(frozen=True, kw_only=True)
class EmissionRuleDraft:
    """A rule as the user is defining it: any field but the type may still be missing.

    Drafts are what the session keeps between visits. Only complete drafts become
    `EmissionRule`s and are computed.
    """

    id: str
    type: EmissionRuleDraftType
    activity: str | None = None
    # E2O rules only: the related objects that emit.
    object_type: str | None = None
    qualifier: str | None = None
    value_kg: float | None = None
    attributes: tuple[AttributeRef, ...] = ()
