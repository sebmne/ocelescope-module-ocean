"""The ordered sOCEL conformance rules V1-V10."""

from socel.validation.rule import ValidationRule
from socel.validation.rules.v1_structure import StructureRule
from socel.validation.rules.v2_references import ReferencesRule
from socel.validation.rules.v3_record_ids import DisjointRecordIdsRule
from socel.validation.rules.v4_intervals import ValidIntervalsRule
from socel.validation.rules.v5_event_ends import ValidEventEndsRule
from socel.validation.rules.v6_interval_overlap import IntervalOverlapRule
from socel.validation.rules.v7_duration_overlap import DurationOverlapRule
from socel.validation.rules.v8_point_overlap import PointOverlapRule
from socel.validation.rules.v9_containment import AcyclicContainmentRule
from socel.validation.rules.v10_taxonomy import TaxonomyMembershipRule

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
