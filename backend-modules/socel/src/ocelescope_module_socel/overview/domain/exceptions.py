class OverviewError(Exception):
    """Base of this slice's errors."""


class NotAnSocelError(OverviewError):
    """The OCEL lacks the sOCEL tables: there is no sOCEL to validate or export."""


class NotConformingError(OverviewError):
    """The sOCEL does not conform, so it is not exported: its file would not be one."""
