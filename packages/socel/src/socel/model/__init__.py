"""The sOCEL as Definition 5.3.2 defines it: `SOCEL`, read-only, and `SOCELEditor`,
which makes one."""

from socel.model.editor import SOCELEditor
from socel.model.socel import SOCEL

__all__ = ["SOCEL", "SOCELEditor"]
