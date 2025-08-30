from typing import Any, Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")

class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper."""
    success: bool
    data: T | None = None
    message: str | None = None
    error_code: str | None = None
    details: dict[str, Any] | None = None

    @classmethod
    def success(cls, data: T = None, message: str = "Success") -> "ApiResponse[T]":
        """Create a successful response."""
        return cls(success=True, data=data, message=message)

    @classmethod
    def error(
        cls,
        message: str,
        error_code: str = "ERROR",
        details: dict[str, Any] | None = None
    ) -> "ApiResponse[None]":
        """Create an error response."""
        return cls(
            success=False,
            message=message,
            error_code=error_code,
            details=details
        )
