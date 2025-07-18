"""
Request models for Blackbird API.

This module contains Pydantic models for validating API request data.
"""
from enum import Enum
from typing import List, Optional, Union

from pydantic import Field, HttpUrl, validator

from ._base import BaseModel


class PlatformCategory(str, Enum):
    """Enum for platform categories."""
    SOCIAL = "social"
    EMAIL = "email"
    PHONE = "phone"
    IP = "ip"


class SearchType(str, Enum):
    """Enum for search types."""
    USERNAME = "username"
    EMAIL = "email"
    PHONE = "phone"
    IP = "ip"


class SearchRequest(BaseModel):
    """Base search request model."""
    query: Union[str, List[str]] = Field(
        ...,
        description="The search term(s) to look up (usernames, emails, etc.)"
    )
    search_type: SearchType = Field(
        default=SearchType.USERNAME,
        description="Type of search to perform"
    )
    filter_expr: Optional[str] = Field(
        None,
        description="Filter expression to refine search results"
    )
    include_nsfw: bool = Field(
        False,
        description="Include NSFW results in the search"
    )
    timeout: int = Field(
        30,
        ge=5,
        le=300,
        description="Timeout in seconds for the search operation"
    )
    use_ai: bool = Field(
        False,
        description="Enable AI analysis of results"
    )
    
    @validator('query')
    def validate_query(cls, v):
        if not v or (isinstance(v, str) and not v.strip()):
            raise ValueError("Query cannot be empty")
        return v


class UsernameSearchRequest(SearchRequest):
    """Request model for username search."""
    search_type: SearchType = Field(
        default=SearchType.USERNAME,
        const=True
    )
    permute: bool = Field(
        False,
        description="Generate username permutations"
    )
    permute_all: bool = Field(
        False,
        description="Generate all possible username permutations"
    )


class EmailSearchRequest(SearchRequest):
    """Request model for email search."""
    search_type: SearchType = Field(
        default=SearchType.EMAIL,
        const=True
    )
    check_breaches: bool = Field(
        True,
        description="Check if email appears in known data breaches"
    )


class ExportFormat(str, Enum):
    """Supported export formats."""
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"
    HTML = "html"


class ExportRequest(BaseModel):
    """Request model for exporting search results."""
    search_id: str = Field(
        ...,
        description="ID of the search to export"
    )
    format: ExportFormat = Field(
        ExportFormat.JSON,
        description="Export format"
    )
    include_raw: bool = Field(
        False,
        description="Include raw HTTP responses in the export"
    )


class FilterCondition(BaseModel):
    """Single filter condition for search refinement."""
    field: str = Field(
        ...,
        description="Field to filter on (e.g., 'name', 'category')"
    )
    operator: str = Field(
        "=",
        description="Comparison operator (e.g., '=', '~', '>', '<', '>=', '<=', '!=')"
    )
    value: str = Field(
        ...,
        description="Value to compare against"
    )


class AdvancedSearchRequest(SearchRequest):
    """Advanced search request with multiple filter conditions."""
    filters: List[FilterCondition] = Field(
        default_factory=list,
        description="List of filter conditions"
    )
    logical_operator: str = Field(
        "and",
        description="Logical operator to combine filters ('and' or 'or')"
    )
    
    @validator('logical_operator')
    def validate_operator(cls, v):
        if v.lower() not in ('and', 'or'):
            raise ValueError("Logical operator must be 'and' or 'or'")
        return v.lower()


class AIConfigRequest(BaseModel):
    """Request model for configuring AI settings."""
    enabled: bool = Field(
        True,
        description="Enable or disable AI analysis"
    )
    api_key: Optional[str] = Field(
        None,
        description="API key for AI service (if required)",
        min_length=10
    )
    daily_limit: int = Field(
        100,
        ge=1,
        le=1000,
        description="Maximum number of AI requests per day"
    )
    analyze_sentiment: bool = Field(
        True,
        description="Enable sentiment analysis in AI results"
    )
    extract_entities: bool = Field(
        True,
        description="Enable entity extraction in AI results"
    )

