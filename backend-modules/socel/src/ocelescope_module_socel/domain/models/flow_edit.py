from math import isfinite
from typing import Self

from pydantic import field_validator, model_validator

from ocelescope_module_socel.domain.exceptions import InvalidFlowEdit, UndefinedFlow
from ocelescope_module_socel.domain.models.base import Model


class FlowEdit(Model):
    """A flow's new definition or deletion; conversion scales every record.

    A deletion needs no replacement name, unit, category, or conversion.
    A negative conversion is allowed: it reverses the flow's direction.
    """

    flow_id: str
    name: str
    unit: str
    category: str | None
    external_ref: str | None = None
    conversion: float | None = None
    delete: bool = False

    @field_validator("name", "unit")
    @classmethod
    def _trim(cls, value: str) -> str:
        return value.strip()

    @field_validator("external_ref")
    @classmethod
    def _reference(cls, value: str | None) -> str | None:
        return value.strip() or None if value is not None else None

    @model_validator(mode="after")
    def _valid_change(self) -> Self:
        if self.delete:
            return self
        if not self.name:
            raise InvalidFlowEdit(f"The flow {self.flow_id!r} needs a name.")
        if not self.unit:
            raise UndefinedFlow(self.name)
        if self.conversion is not None and (not isfinite(self.conversion) or self.conversion == 0):
            raise InvalidFlowEdit(
                f"The conversion of {self.flow_id!r} must be a number other than 0."
            )
        return self
