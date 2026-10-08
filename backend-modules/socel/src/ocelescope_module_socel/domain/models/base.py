from dataclasses import dataclass
from typing import dataclass_transform


@dataclass_transform(frozen_default=True, kw_only_default=True)
class Model:
    """Base of all domain models: plain data as one immutable, keyword-only
    dataclass. A subclass only lists its fields."""

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        dataclass(frozen=True, kw_only=True)(cls)
