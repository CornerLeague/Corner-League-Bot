from typing import Generic, TypeVar, Optional, Any, Dict
from pydantic import BaseModel

T = TypeVar('T')

class ApiResponse(BaseModel, Generic[T]):
    """Standardized API response wrapper."""
    success: bool
    data: Optional[T] = None
    message: Optional[str] = None
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    
    @classmethod
    def success(cls, data: T = None, message: str = "Success") -> "ApiResponse[T]":
        """Create a successful response."""
        return cls(success=True, data=data, message=message)
    
    @classmethod
    def error(
        cls, 
        message: str, 
        error_code: str = "ERROR", 
        details: Optional[Dict[str, Any]] = None
    ) -> "ApiResponse[None]":
        """Create an error response."""
        return cls(
            success=False, 
            message=message, 
            error_code=error_code, 
            details=details
        )
