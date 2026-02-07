"""Standard API response envelope."""

from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class Meta(BaseModel):
    """Response metadata."""

    request_id: str | None = None


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
