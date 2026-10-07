import duckdb
from ocelescope import OCEL, Extension

from socel.managers import (
    ClassificationsManager,
    FlowInstancesManager,
    FlowsManager,
    MeasurementsManager,
)
from socel.schema import TABLES
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


class SOCEL(OCEL):
    """An OCEL that passed the sOCEL conformance rules.

    :meth:`from_ocel` views an open OCEL as an sOCEL: it runs :meth:`validate` and
    raises an ``OCELExtensionError`` with the reason if the log is none. The view
    uses the same database as the source OCEL and adds sOCEL-specific managers.
    """

    extension = Extension(
        name="socel",
        label="sOCEL",
        tables={
            table.name: [
                (column.name, column.database_type) for column in table.columns
            ]
            for table in TABLES
        },
    )

    def __init__(
        self,
        connection: duckdb.DuckDBPyConnection,
        taxonomies: SOCELTaxonomies = DEFAULT_TAXONOMY,
    ) -> None:
        super().__init__(connection)
        self.taxonomies = taxonomies
        self.flows = FlowsManager(self)
        self.flow_instances = FlowInstancesManager(self)
        self.measurements = MeasurementsManager(self)
        self.classifications = ClassificationsManager(self)

    def validate(self) -> None:
        """Raise unless the log has the sOCEL tables and passes the conformance rules.

        Raises:
            SOCELValidationError: If an applicable conformance rule fails.
        """
        super().validate()
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
        result = pipeline.validate(self, self.taxonomies)
        result.unwrap_or_raise(SOCELValidationError)
