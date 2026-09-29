"""sOCEL: the sustainability-enriched OCEL (Heinisch 2026).

An OCEL 2.0 log extended by handling units and operations, event end times,
flows, flow instances with their interval and event-linked records, and the
containment of flow instances (Definition 5.3.2), serialized as four more SQLite
tables and reserved attributes (Section 5.5). Built on Ocelescope's OCEL,
independent of the Ocelescope backend and its modules.

    from socel import SOCEL, SOCELEditor

    socel = SOCEL.read("plant.sqlite")        # validated: V1–V9
    socel.handling_units, socel.operations, socel.records
    changed = SOCELEditor(socel).add_flow("water", "l", "material.water").build()
"""

from socel.analysis import (
    Allocation,
    Attribution,
    allocate,
    attribute,
    carry,
    creation_values,
    flow_quantities,
    impact,
    parents,
    unit_attributes,
    unit_relation_qualifiers,
)
from socel.errors import (
    EditorClosedError,
    InvalidClassError,
    LineageError,
    NotAnSocelError,
    SocelError,
    SocelWriteError,
)
from socel.model import SOCEL, SOCELEditor
from socel.taxonomy import (
    FLOW_CATEGORIES,
    HANDLING_UNITS,
    OPERATIONS,
    PROCESS_RESOURCES,
    Taxonomy,
    TaxonomyPath,
)
from socel.validation import (
    CONFORMANCE,
    Check,
    CheckResult,
    Finding,
    Profile,
    RowCheck,
    Severity,
    SocelValidationError,
    Status,
    ValidationReport,
)

__all__ = [
    "Allocation",
    "Attribution",
    "LineageError",
    "allocate",
    "attribute",
    "carry",
    "creation_values",
    "flow_quantities",
    "unit_relation_qualifiers",
    "impact",
    "parents",
    "unit_attributes",
    "CONFORMANCE",
    "FLOW_CATEGORIES",
    "HANDLING_UNITS",
    "OPERATIONS",
    "PROCESS_RESOURCES",
    "SOCEL",
    "Check",
    "CheckResult",
    "EditorClosedError",
    "Finding",
    "InvalidClassError",
    "NotAnSocelError",
    "Profile",
    "RowCheck",
    "SOCELEditor",
    "Severity",
    "SocelError",
    "SocelValidationError",
    "SocelWriteError",
    "Status",
    "Taxonomy",
    "TaxonomyPath",
    "ValidationReport",
]
