from typing import ClassVar, Self

from ocelescope import OCEL, OCELExtension

from socel.managers import (
    ClassificationsManager,
    FlowInstancesManager,
    FlowsManager,
    MeasurementsManager,
)
from socel.taxonomy import DEFAULT_TAXONOMY, SOCELTaxonomies
from socel.validation import SOCELValidationError, ValidationPipeline
from socel.validation.rules import (
    AcyclicContainmentRule,
    DisjointRecordIdsRule,
    DurationOverlapRule,
    IntervalOverlapRule,
    PointOverlapRule,
    ReferencesRule,
    StructureRule,
    TaxonomyMembershipRule,
    ValidEventEndsRule,
    ValidIntervalsRule,
)


class SOCEL(OCELExtension):
    """An OCEL that passed the sOCEL conformance rules.

    Construction goes through :meth:`from_ocel`. The wrapper borrows the OCEL;
    it neither copies nor closes its database connection.
    """

    id: ClassVar[str] = "socel"
    label: ClassVar[str] = "sOCEL"

    def __init__(
        self,
        ocel: OCEL,
        taxonomies: SOCELTaxonomies = DEFAULT_TAXONOMY,
    ) -> None:
        self._ocel = ocel
        self.taxonomies = taxonomies
        self.flows = FlowsManager(ocel)
        self.flow_instances = FlowInstancesManager(ocel)
        self.measurements = MeasurementsManager(ocel)
        self.classifications = ClassificationsManager(ocel)

    @classmethod
    def read(
        cls,
        *args,
        taxonomies: SOCELTaxonomies = DEFAULT_TAXONOMY,
        **kwargs,
    ) -> Self:
        return cls.from_ocel(
            OCEL.read(*args, **kwargs),
            taxonomies=taxonomies,
        )

    @classmethod
    def from_ocel(
        cls,
        ocel: OCEL,
        *,
        taxonomies: SOCELTaxonomies = DEFAULT_TAXONOMY,
    ) -> Self:
        """Validate ``ocel`` and return its typed sOCEL view.

        Raises:
            SOCELValidationError: If an applicable conformance rule fails.
        """
        instance = cls(ocel, taxonomies)
        instance.validate()
        return instance

    @property
    def ocel(self) -> OCEL:
        """The underlying Ocelescope OCEL."""
        return self._ocel

    def validate(self) -> None:
        """Revalidate after code outside this wrapper may have changed the OCEL."""
        pipeline = ValidationPipeline(
            rules=[
                StructureRule(),
                ReferencesRule(),
                DisjointRecordIdsRule(),
                ValidIntervalsRule(),
                ValidEventEndsRule(),
                IntervalOverlapRule(),
                DurationOverlapRule(),
                PointOverlapRule(),
                AcyclicContainmentRule(),
                TaxonomyMembershipRule(),
            ]
        )
        result = pipeline.validate(self._ocel, self.taxonomies)
        result.unwrap_or_raise(SOCELValidationError)
