"""Exceptions. Problems in the data are findings of a validation; an sOCEL that
does not conform is refused as a whole with `SocelValidationError`, which lives
next to the report it carries (socel.validation.report)."""


class SocelError(Exception):
    """Base of all errors raised by this package."""


class NotAnSocelError(SocelError):
    """An sOCEL table was used that the log does not have."""


class EditorClosedError(SocelError):
    """The editor has built its sOCEL already; start a new one to change it."""


class SocelWriteError(SocelError):
    """The sOCEL breaks a constraint its SQLite serialization declares."""


class InvalidClassError(SocelError, ValueError):
    """A string is no dot-separated class path, e.g. `pr..x` (for TaxonomyPath).

    Classes stored in an sOCEL are free text; this concerns reading one as a path
    of the taxonomy."""
