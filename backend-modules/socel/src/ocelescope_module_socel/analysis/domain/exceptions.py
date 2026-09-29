class AnalysisError(Exception):
    """Base of this slice's errors."""


class NotAnSocelError(AnalysisError):
    """The OCEL lacks the sOCEL tables: there are no records to analyze."""


class UnknownFlowError(AnalysisError):
    """The sOCEL has no flow of that id."""
