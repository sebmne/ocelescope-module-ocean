"""The ordered sOCEL conformance rules V1-V10."""

from ocelescope_module_socel.infrastructure.conformance.rule import ValidationRule
from ocelescope_module_socel.infrastructure.conformance.rules.v1_structure import StructureRule
from ocelescope_module_socel.infrastructure.conformance.rules.v2_references import ReferencesRule
from ocelescope_module_socel.infrastructure.conformance.rules.v3_record_ids import (
    DisjointRecordIdsRule,
)
from ocelescope_module_socel.infrastructure.conformance.rules.v4_intervals import ValidIntervalsRule
from ocelescope_module_socel.infrastructure.conformance.rules.v5_event_ends import (
    ValidEventEndsRule,
)
from ocelescope_module_socel.infrastructure.conformance.rules.v6_interval_overlap import (
    IntervalOverlapRule,
)
from ocelescope_module_socel.infrastructure.conformance.rules.v7_duration_overlap import (
    DurationOverlapRule,
)
from ocelescope_module_socel.infrastructure.conformance.rules.v8_point_overlap import (
    PointOverlapRule,
)
from ocelescope_module_socel.infrastructure.conformance.rules.v9_containment import (
    AcyclicContainmentRule,
)
from ocelescope_module_socel.infrastructure.conformance.rules.v10_taxonomy import (
    TaxonomyMembershipRule,
)

__all__ = [
    "AcyclicContainmentRule",
    "DisjointRecordIdsRule",
    "DurationOverlapRule",
    "IntervalOverlapRule",
    "PointOverlapRule",
    "ReferencesRule",
    "StructureRule",
    "TaxonomyMembershipRule",
    "ValidEventEndsRule",
    "ValidIntervalsRule",
    "ValidationRule",
]
