"""Standard API response envelope."""

import math
from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    """Response metadata."""

    request_id: str | None = None


class PaginationMeta(BaseModel):
    """Pagination metadata for list endpoints."""

    page: int
    per_page: int
    total: int
    total_pages: int


class ApiResponse(BaseModel, Generic[T]):
    """Standard API response envelope.

    Attributes:
        data: The response payload.
        meta: Optional metadata.
        errors: List of error messages, if any.
    """

    data: T | None = None
    meta: Meta | None = None
    errors: list[str] | None = None


class PaginatedApiResponse(BaseModel, Generic[T]):
    """Paginated API response envelope for list endpoints.

    Attributes:
        data: List of items.
        meta: Pagination metadata.
        errors: List of error messages, if any.
    """

    data: list[T]
    meta: PaginationMeta
    errors: list[str] | None = None

    @classmethod
    def create(
        cls, items: list[T], total: int, page: int, per_page: int
    ) -> "PaginatedApiResponse[T]":
        """Build a paginated response from items and totals."""
        return cls(
            data=items,
            meta=PaginationMeta(
                page=page,
                per_page=per_page,
                total=total,
                total_pages=max(1, math.ceil(total / per_page)),
            ),
        )
