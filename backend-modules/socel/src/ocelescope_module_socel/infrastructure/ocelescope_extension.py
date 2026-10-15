from ocelescope import OCEL, Extension

from ocelescope_module_socel.infrastructure.conformance import (
    SocelValidationError,
    ValidationPipeline,
)
from ocelescope_module_socel.infrastructure.conformance.rules import (
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
from ocelescope_module_socel.infrastructure.schema import TABLES


class SOCEL(OCEL):
    """An OCEL that passed the sOCEL conformance rules.

    :meth:`from_ocel` views an open OCEL as an sOCEL: it runs :meth:`validate` and
    raises an ``OCELExtensionError`` with the reason if the log is none. The view
    uses the same database as the source OCEL. The host owns the source lifetime.
    """

    extension = Extension(
        name="socel",
        label="sOCEL",
        tables={
            table.name: [(column.name, column.database_type) for column in table.columns]
            for table in TABLES
        },
    )

    def validate(self) -> None:
        """Raise unless the log passes the sOCEL conformance rules.

        This replaces the base check of the declared tables: the structure rule
        (V1) requires the same tables and columns, and names all that are missing
        where the base check stops at the first.

        Raises:
            SocelValidationError: If an applicable conformance rule fails.
        """
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
        result = pipeline.validate(self)
        result.unwrap_or_raise(SocelValidationError)
