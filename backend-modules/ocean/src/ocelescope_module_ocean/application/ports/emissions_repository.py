from typing import Protocol

from ocelescope_module_ocean.domain.models.allocation import ObjectEmissions
from ocelescope_module_ocean.domain.models.emissions import ProcessEmissions


class EmissionsRepository(Protocol):
    """Keeps the emissions computed and allocated for each OCEL between requests."""

    def save(self, ocel_id: str, emissions: ProcessEmissions) -> None:
        """Stores new emissions; an allocation of the previous ones is discarded."""
        ...

    def get(self, ocel_id: str) -> ProcessEmissions | None:
        """The emissions computed for the OCEL, or None if none were computed yet."""
        ...

    def save_object_emissions(self, ocel_id: str, object_emissions: ObjectEmissions) -> None: ...

    def get_object_emissions(self, ocel_id: str) -> ObjectEmissions | None:
        """The current allocation, or None if the emissions were not allocated yet."""
        ...
