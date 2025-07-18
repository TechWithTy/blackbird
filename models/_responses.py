"""
Response models for Blackbird API.

This module contains Pydantic models for API response data.
"""
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Union

from pydantic import Field, HttpUrl

from ._base import BaseModel, BaseResponse


class PlatformCategory(str, Enum):
    """Categories for social media platforms."""
    SOCIAL = "social"
    PROFESSIONAL = "professional"
    CODE = "code"
    FORUM = "forum"
    GAMING = "gaming"
    SHOPPING = "shopping"
    MUSIC = "music"
    VIDEO = "video"
    BLOG = "blog"
    OTHER = "other"


class AccountStatus(str, Enum):
    """Status of an account on a platform."""
    FOUND = "found"
    NOT_FOUND = "not_found"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"
    PRIVATE = "private"
    SUSPENDED = "suspended"


class PlatformInfo(BaseModel):
    """Information about a platform where an account might exist."""
    name: str = Field(..., description="Name of the platform")
    url: Optional[HttpUrl] = Field(None, description="Base URL of the platform")
    category: PlatformCategory = Field(PlatformCategory.OTHER, description="Platform category")
    is_nsfw: bool = Field(False, description="Whether the platform is NSFW")
    requires_auth: bool = Field(False, description="If authentication is required to check this platform")


class AccountResult(BaseModel):
    """Result of checking an account on a single platform."""
    platform: str = Field(..., description="Name of the platform")
    url: Optional[HttpUrl] = Field(None, description="Direct URL to the account if found")
    status: AccountStatus = Field(..., description="Status of the account check")
    http_status: Optional[int] = Field(None, description="HTTP status code received")
    error: Optional[str] = Field(None, description="Error message if status is ERROR")
    extracted_data: Optional[Dict[str, str]] = Field(
        None,
        description="Additional data extracted from the profile (e.g., name, bio, location)"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When this check was performed"
    )
    response_time: Optional[float] = Field(
        None,
        description="Time taken to check this platform in seconds"
    )


class SearchResult(BaseModel):
    """Results of a search operation for a single query."""
    query: str = Field(..., description="The search query")
    search_type: str = Field(..., description="Type of search performed")
    total_platforms: int = Field(..., description="Total number of platforms checked")
    accounts_found: int = Field(..., description="Number of platforms where the account was found")
    execution_time: float = Field(..., description="Total execution time in seconds")
    results: List[AccountResult] = Field(
        default_factory=list,
        description="List of account check results"
    )
    search_id: str = Field(
        ...,
        description="Unique identifier for this search"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the search was performed"
    )


class AIAnalysis(BaseModel):
    """Results of AI analysis on search results."""
    summary: str = Field(..., description="Summary of the analysis")
    behavioral_insights: Optional[List[str]] = Field(
        None,
        description="List of behavioral insights"
    )
    risk_assessment: Optional[Dict[str, float]] = Field(
        None,
        description="Risk assessment scores (e.g., {'privacy_risk': 0.75})"
    )
    confidence: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Confidence score of the analysis (0.0 to 1.0)"
    )
    generated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the analysis was generated"
    )


class SearchResponse(BaseResponse[SearchResult]):
    """API response for search operations."""
    ai_analysis: Optional[AIAnalysis] = Field(
        None,
        description="AI analysis of the search results, if requested"
    )
    has_more: bool = Field(
        False,
        description="Whether there are more results available"
    )
    next_page: Optional[str] = Field(
        None,
        description="Token for the next page of results"
    )


class ExportResponse(BaseModel):
    """Response model for export operations."""
    export_id: str = Field(..., description="Unique identifier for this export")
    format: str = Field(..., description="Export format (e.g., 'json', 'csv', 'pdf')")
    status: str = Field(..., description="Export status ('processing', 'completed', 'failed')")
    download_url: Optional[HttpUrl] = Field(
        None,
        description="URL to download the exported file when ready"
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="When the download URL will expire"
    )
    size_bytes: Optional[int] = Field(
        None,
        description="Size of the exported file in bytes"
    )


class PlatformListResponse(BaseResponse[Dict[PlatformCategory, List[PlatformInfo]]]):
    """Response containing the list of supported platforms."""
    total_platforms: int = Field(
        ...,
        description="Total number of supported platforms"
    )
    last_updated: datetime = Field(
        ...,
        description="When the platform list was last updated"
    )


class UsageMetrics(BaseModel):
    """Usage metrics for the API."""
    searches_today: int = Field(
        ...,
        ge=0,
        description="Number of searches performed today"
    )
    daily_limit: int = Field(
        ...,
        ge=1,
        description="Daily search limit"
    )
    ai_requests_today: int = Field(
        ...,
        ge=0,
        description="Number of AI analysis requests made today"
    )
    ai_daily_limit: int = Field(
        ...,
        ge=1,
        description="Daily AI request limit"
    )
    reset_time: datetime = Field(
        ...,
        description="When the usage counters will reset"
    )


class HealthStatus(str, Enum):
    """Health status of the service."""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HealthCheckResponse(BaseResponse):
    """Health check response."""
    status: HealthStatus = Field(..., description="Overall health status")
    version: str = Field(..., description="API version")
    uptime_seconds: float = Field(..., description="Service uptime in seconds")
    database_status: HealthStatus = Field(..., description="Database health status")
    cache_status: HealthStatus = Field(..., description="Cache health status")
    external_services: Dict[str, HealthStatus] = Field(
        ...,
        description="Status of external services"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the health check was performed"
    )
