from typing import Protocol

from ocelescope_module_socel.domain.models.flow_quantities import FlowQuantity, Period


class FlowAnalysis(Protocol):
    """Aggregate quantities for the log/view bound by the entry adapter."""

    def quantities(self, period: Period) -> tuple[FlowQuantity, ...]:
        """Return directional amounts per flow and calendar period.

        Exclude records already covered by a containing instance's records.
        """
        ...
