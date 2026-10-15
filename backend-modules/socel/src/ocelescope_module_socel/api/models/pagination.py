from collections.abc import Sequence
from typing import Any, Self

from pydantic import Field

from ocelescope_module_socel.api.schema import ApiModel

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200


class Pagination(ApiModel):
    """Shared query parameters and the API's page-size policy."""

    offset: int = Field(default=0, ge=0)
    limit: int = Field(default=DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE)


class Page[T](ApiModel):
    items: tuple[T, ...]
    total: int = Field(ge=0)
    offset: int = Field(ge=0)
    limit: int = Field(ge=1, le=MAX_PAGE_SIZE)

    @classmethod
    def from_result(
        cls, pagination: Pagination, items: Sequence[T], total: int, **context: Any
    ) -> Self:
        """Wrap domain items, including extra context declared by a page subtype."""
        return cls(
            items=tuple(items),
            total=total,
            offset=pagination.offset,
            limit=pagination.limit,
            **context,
        )
