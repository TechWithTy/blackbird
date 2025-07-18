"""
Exception models for Blackbird API.

This module contains custom exceptions and error response models.
"""
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import Field

from ._base import BaseErrorResponse, BaseModel


class ErrorCode(str, Enum):
    """Standard error codes for the API."""
    # General errors (1000-1999)
    VALIDATION_ERROR = "validation_error"
    AUTHENTICATION_ERROR = "authentication_error"
    PERMISSION_DENIED = "permission_denied"
    NOT_FOUND = "not_found"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    INTERNAL_SERVER_ERROR = "internal_server_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT_ERROR = "timeout_error"
    
    # Search-related errors (2000-2999)
    INVALID_SEARCH_QUERY = "invalid_search_query"
    SEARCH_LIMIT_EXCEEDED = "search_limit_exceeded"
    UNSUPPORTED_SEARCH_TYPE = "unsupported_search_type"
    
    # AI-related errors (3000-3999)
    AI_SERVICE_UNAVAILABLE = "ai_service_unavailable"
    AI_QUOTA_EXCEEDED = "ai_quota_exceeded"
    AI_PROCESSING_ERROR = "ai_processing_error"
    
    # Export-related errors (4000-4999)
    EXPORT_FAILED = "export_failed"
    EXPORT_FORMAT_UNSUPPORTED = "export_format_unsupported"
    
    # Authentication & Authorization errors (5000-5999)
    INVALID_API_KEY = "invalid_api_key"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"
    ACCOUNT_SUSPENDED = "account_suspended"


class ErrorLocation(BaseModel):
    """Location of an error in the request."""
    field: Optional[str] = Field(
        None,
        description="Name of the field that caused the error"
    )
    pointer: Optional[str] = Field(
        None,
        description="JSON pointer to the location of the error"
    )
    line: Optional[int] = Field(
        None,
        description="Line number where the error occurred"
    )
    column: Optional[int] = Field(
        None,
        description="Column number where the error occurred"
    )


class ErrorDetail(BaseModel):
    """Detailed information about an error."""
    code: ErrorCode = Field(
        ...,
        description="Machine-readable error code"
    )
    message: str = Field(
        ...,
        description="Human-readable error message"
    )
    target: Optional[str] = Field(
        None,
        description="The target of the error (e.g., the field name)"
    )
    location: Optional[ErrorLocation] = Field(
        None,
        description="Location of the error in the request"
    )
    help_url: Optional[str] = Field(
        None,
        description="URL to documentation about this error"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional metadata about the error"
    )


class APIError(Exception):
    """Base exception for all API errors."""
    def __init__(
        self,
        status_code: int,
        error: ErrorDetail,
        headers: Optional[Dict[str, str]] = None
    ):
        self.status_code = status_code
        self.error = error
        self.headers = headers or {}
        super().__init__(error.message)
    
    def to_response(self) -> 'ErrorResponse':
        """Convert the exception to an error response."""
        return ErrorResponse(
            success=False,
            error=self.error,
            message=self.error.message,
            status_code=self.status_code
        )


class ValidationError(APIError):
    """Raised when request validation fails."""
    def __init__(
        self,
        errors: List[Dict[str, Any]],
        headers: Optional[Dict[str, str]] = None
    ):
        error_details = []
        
        for error in errors:
            loc = error.get('loc', [])
            field = loc[-1] if loc else 'request'
            
            error_details.append(ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message=error.get('msg', 'Validation error'),
                target=str(field),
                location=ErrorLocation(
                    field=field,
                    pointer=f"/{'/'.join(str(loc) for loc in loc)}" if loc else None
                ),
                metadata={
                    'type': error.get('type'),
                    'ctx': error.get('ctx')
                }
            ))
        
        super().__init__(
            status_code=422,
            error=ErrorDetail(
                code=ErrorCode.VALIDATION_ERROR,
                message='One or more validation errors occurred',
                metadata={'errors': [e.dict() for e in error_details]}
            ),
            headers=headers
        )
        self.details = error_details


class NotFoundError(APIError):
    """Raised when a requested resource is not found."""
    def __init__(
        self,
        resource: str = 'resource',
        resource_id: Optional[Union[str, int]] = None,
        headers: Optional[Dict[str, str]] = None
    ):
        identifier = f" '{resource_id}'" if resource_id is not None else ''
        message = f"{resource}{identifier} not found"
        
        super().__init__(
            status_code=404,
            error=ErrorDetail(
                code=ErrorCode.NOT_FOUND,
                message=message
            ),
            headers=headers
        )


class RateLimitError(APIError):
    """Raised when the rate limit is exceeded."""
    def __init__(
        self,
        limit: int,
        remaining: int,
        reset: int,
        headers: Optional[Dict[str, str]] = None
    ):
        headers = headers or {}
        headers.update({
            'X-RateLimit-Limit': str(limit),
            'X-RateLimit-Remaining': str(remaining),
            'X-RateLimit-Reset': str(reset)
        })
        
        super().__init__(
            status_code=429,
            error=ErrorDetail(
                code=ErrorCode.RATE_LIMIT_EXCEEDED,
                message='Rate limit exceeded',
                metadata={
                    'limit': limit,
                    'remaining': remaining,
                    'reset': reset
                }
            ),
            headers=headers
        )


class ErrorResponse(BaseErrorResponse[ErrorDetail]):
    """Standard error response format."""
    status_code: int = Field(
        500,
        description="HTTP status code"
    )
    
    class Config:
        schema_extra = {
            "example": {
                "success": False,
                "error": {
                    "code": "validation_error",
                    "message": "One or more validation errors occurred",
                    "target": "request",
                    "metadata": {
                        "errors": [
                            {
                                "code": "validation_error",
                                "message": "field required",
                                "target": "username",
                                "location": {
                                    "field": "username",
                                    "pointer": "/username"
                                }
                            }
                        ]
                    }
                },
                "message": "One or more validation errors occurred",
                "timestamp": "2023-04-01T12:00:00Z",
                "status_code": 422
            }
        }


# Common exceptions for easier imports
class AuthenticationError(APIError):
    """Raised when authentication fails."""
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            status_code=401,
            error=ErrorDetail(
                code=ErrorCode.AUTHENTICATION_ERROR,
                message=message
            )
        )


class PermissionDeniedError(APIError):
    """Raised when the user doesn't have permission to perform an action."""
    def __init__(self, message: str = "Permission denied"):
        super().__init__(
            status_code=403,
            error=ErrorDetail(
                code=ErrorCode.PERMISSION_DENIED,
                message=message
            )
        )


class InternalServerError(APIError):
    """Raised when an unexpected error occurs on the server."""
    def __init__(self, message: str = "An internal server error occurred"):
        super().__init__(
            status_code=500,
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_SERVER_ERROR,
                message=message
            )
        )


class ServiceUnavailableError(APIError):
    """Raised when a required service is unavailable."""
    def __init__(self, message: str = "Service temporarily unavailable"):
        super().__init__(
            status_code=503,
            error=ErrorDetail(
                code=ErrorCode.SERVICE_UNAVAILABLE,
                message=message
            )
        )


class AIQuotaExceededError(APIError):
    """Raised when the AI service quota is exceeded."""
    def __init__(self, message: str = "AI service quota exceeded"):
        super().__init__(
            status_code=429,
            error=ErrorDetail(
                code=ErrorCode.AI_QUOTA_EXCEEDED,
                message=message
            )
        )
