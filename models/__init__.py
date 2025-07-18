"""
Blackbird API Models

This package contains the Pydantic models for the Blackbird API.
"""

from ._base import BaseModel, BaseResponse, BaseErrorResponse
from ._requests import (
    PlatformCategory,
    SearchType,
    SearchRequest,
    UsernameSearchRequest,
    EmailSearchRequest,
    ExportFormat,
    ExportRequest,
    FilterOperator,
    FilterCondition,
    AdvancedSearchRequest,
    AIModel,
    AIConfigRequest,
)
from ._responses import (
    ResponseStatus,
    PlatformInfo,
    AccountResult,
    SearchResult,
    AIAnalysis,
    ExportResponse as ExportResponseModel,  # Alias to avoid conflict
    PlatformListResponse,
    UsageMetrics,
    HealthCheckResponse,
)
from ._exceptions import (
    ErrorCode,
    APIError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
    PermissionDeniedError,
    RateLimitError,
    ServiceUnavailableError,
    InvalidRequestError,
    ExportError,
)

__all__ = [
    # Base
    "BaseModel",
    "BaseResponse",
    "BaseErrorResponse",
    # Requests
    "PlatformCategory",
    "SearchType",
    "SearchRequest",
    "UsernameSearchRequest",
    "EmailSearchRequest",
    "ExportFormat",
    "ExportRequest",
    "FilterOperator",
    "FilterCondition",
    "AdvancedSearchRequest",
    "AIModel",
    "AIConfigRequest",
    # Responses
    "ResponseStatus",
    "PlatformInfo",
    "AccountResult",
    "SearchResult",
    "AIAnalysis",
    "ExportResponseModel",
    "PlatformListResponse",
    "UsageMetrics",
    "HealthCheckResponse",
    # Exceptions
    "ErrorCode",
    "APIError",
    "ValidationError",
    "NotFoundError",
    "AuthenticationError",
    "PermissionDeniedError",
    "RateLimitError",
    "ServiceUnavailableError",
    "InvalidRequestError",
    "ExportError",
]
