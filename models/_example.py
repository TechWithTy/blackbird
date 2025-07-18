"""
FastAPI Integration Example

This module demonstrates how to use the Blackbird models with FastAPI.
It shows common API endpoints and how to handle requests and responses.
"""
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Depends, status, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import HttpUrl

# Import our models
from ._base import BaseResponse
from ._requests import (
    SearchRequest,
    UsernameSearchRequest,
    EmailSearchRequest,
    ExportFormat,
    ExportRequest,
    AIConfigRequest,
    PlatformCategory,
)
from ._responses import (
    SearchResult,
    AccountResult,
    AccountStatus,
    PlatformInfo,
    UsageMetrics,
    HealthStatus,
    HealthCheckResponse,
    AIAnalysis,
)
from ._exceptions import (
    APIError,
    ValidationError,
    NotFoundError,
    RateLimitError,
    AuthenticationError,
    PermissionDeniedError,
)

# Initialize FastAPI app
app = FastAPI(
    title="Blackbird API",
    description="API for Blackbird OSINT Tool",
    version="1.0.0",
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mock database and state
class Database:
    """Mock database for demonstration purposes."""
    searches = {}
    platforms = [
        PlatformInfo(
            name="Twitter",
            url="https://twitter.com",
            category=PlatformCategory.SOCIAL,
        ),
        PlatformInfo(
            name="GitHub",
            url="https://github.com",
            category=PlatformCategory.CODE,
        ),
        # Add more platforms as needed
    ]
    
    @classmethod
    def save_search(cls, search_id: str, result: SearchResult):
        cls.searches[search_id] = result
        return result
    
    @classmethod
    def get_search(cls, search_id: str) -> Optional[SearchResult]:
        return cls.searches.get(search_id)

# Mock AI Service
class AIService:
    """Mock AI service for demonstration."""
    
    @staticmethod
    def analyze(search_result: SearchResult) -> AIAnalysis:
        """Generate AI analysis for search results."""
        return AIAnalysis(
            summary=f"AI analysis for search '{search_result.search_id}'",
            behavioral_insights=["User is active on multiple platforms"],
            risk_assessment={"privacy_risk": 0.3, "reputation_risk": 0.1},
            confidence=0.85,
        )

# Exception Handler
@app.exception_handler(APIError)
async def api_error_handler(request: Request, exc: APIError):
    """Handle API errors consistently."""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.error.dict(),
        headers=exc.headers,
    )

# Middleware for rate limiting
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Simple rate limiting middleware."""
    # In a real app, you'd check rate limits here
    response = await call_next(request)
    return response

# API Endpoints
@app.get("/health", response_model=HealthCheckResponse)
async def health_check():
    """Health check endpoint."""
    return HealthCheckResponse(
        status=HealthStatus.HEALTHY,
        version="1.0.0",
        uptime_seconds=3600,  # Example value
        database_status=HealthStatus.HEALTHY,
        cache_status=HealthStatus.HEALTHY,
        external_services={
            "ai_service": HealthStatus.HEALTHY,
            "database": HealthStatus.HEALTHY,
        },
    )

@app.post("/api/v1/search/username", response_model=BaseResponse[SearchResult])
async def search_username(request: UsernameSearchRequest):
    """Search for a username across multiple platforms."""
    # In a real app, you would perform the actual search here
    search_id = f"search_{datetime.utcnow().timestamp()}"
    
    # Mock search results
    results = [
        AccountResult(
            platform="Twitter",
            url=f"https://twitter.com/{request.query}",
            status=AccountStatus.FOUND,
            http_status=200,
            extracted_data={"followers": "1.2K", "tweets": "456"},
        ),
        AccountResult(
            platform="GitHub",
            url=f"https://github.com/{request.query}",
            status=AccountStatus.NOT_FOUND,
            http_status=404,
        ),
    ]
    
    # Create search result
    search_result = SearchResult(
        query=request.query,
        search_type="username",
        total_platforms=len(Database.platforms),
        accounts_found=len([r for r in results if r.status == AccountStatus.FOUND]),
        execution_time=1.5,  # seconds
        results=results,
        search_id=search_id,
    )
    
    # Apply AI analysis if requested
    ai_analysis = None
    if getattr(request, "use_ai", False):
        ai_analysis = AIService.analyze(search_result)
    
    # Save to database
    Database.save_search(search_id, search_result)
    
    # Return response
    return BaseResponse[SearchResult](
        data=search_result,
        message="Search completed successfully",
    )

@app.post("/api/v1/search/email", response_model=BaseResponse[SearchResult])
async def search_email(request: EmailSearchRequest):
    """Search for an email across multiple platforms."""
    # Similar to username search but for emails
    search_id = f"search_{datetime.utcnow().timestamp()}"
    
    # Mock results
    results = [
        AccountResult(
            platform="Gravatar",
            url=f"https://gravatar.com/{request.query}",
            status=AccountStatus.FOUND,
            http_status=200,
        ),
    ]
    
    search_result = SearchResult(
        query=request.query,
        search_type="email",
        total_platforms=len(Database.platforms),
        accounts_found=len([r for r in results if r.status == AccountStatus.FOUND]),
        execution_time=1.2,
        results=results,
        search_id=search_id,
    )
    
    Database.save_search(search_id, search_result)
    
    return BaseResponse[SearchResult](
        data=search_result,
        message="Email search completed",
    )

@app.get("/api/v1/search/{search_id}", response_model=BaseResponse[SearchResult])
async def get_search_results(search_id: str):
    """Retrieve search results by ID."""
    result = Database.get_search(search_id)
    if not result:
        raise NotFoundError(resource="search", resource_id=search_id)
    
    return BaseResponse[SearchResult](
        data=result,
        message="Search results retrieved",
    )

@app.post("/api/v1/export", response_model=BaseResponse[dict])
async def export_results(request: ExportRequest):
    """Export search results in the specified format."""
    result = Database.get_search(request.search_id)
    if not result:
        raise NotFoundError(resource="search", resource_id=request.search_id)
    
    # In a real app, you would generate the export file here
    export_data = {
        "search_id": request.search_id,
        "format": request.format,
        "status": "completed",
        "download_url": f"https://api.blackbird.example.com/exports/{request.search_id}.{request.format}",
        "expires_at": (datetime.utcnow() + timedelta(days=7)).isoformat(),
    }
    
    return BaseResponse[dict](
        data=export_data,
        message="Export completed successfully",
    )

@app.get("/api/v1/platforms", response_model=BaseResponse[List[PlatformInfo]])
async def list_platforms(
    category: Optional[PlatformCategory] = None,
    include_nsfw: bool = False
):
    """List all supported platforms, optionally filtered by category."""
    platforms = Database.platforms
    
    if category:
        platforms = [p for p in platforms if p.category == category]
    
    if not include_nsfw:
        platforms = [p for p in platforms if not getattr(p, "is_nsfw", False)]
    
    return BaseResponse[List[PlatformInfo]](
        data=platforms,
        message=f"Found {len(platforms)} platforms",
    )

# Example of a protected endpoint
@app.get("/api/v1/usage", response_model=BaseResponse[UsageMetrics])
async def get_usage(api_key: str = Query(..., description="API key for authentication")):
    """Get current usage statistics for the API key."""
    # In a real app, you would validate the API key and get actual usage
    if api_key != "valid_api_key":
        raise AuthenticationError("Invalid API key")
    
    return BaseResponse[UsageMetrics](
        data=UsageMetrics(
            searches_today=5,
            daily_limit=100,
            ai_requests_today=2,
            ai_daily_limit=50,
            reset_time=datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            ) + timedelta(days=1),
        ),
        message="Usage metrics retrieved",
    )

# Example of error handling
@app.get("/api/v1/error/validation")
async def trigger_validation_error():
    """Example endpoint that triggers a validation error."""
    # This would normally be handled by FastAPI's validation
    raise ValidationError([{"loc": ["query", "page"], "msg": "must be greater than 0"}])

@app.get("/api/v1/error/rate-limit")
async def trigger_rate_limit():
    """Example endpoint that triggers a rate limit error."""
    raise RateLimitError(
        limit=100,
        remaining=0,
        reset=int((datetime.utcnow() + timedelta(hours=1)).timestamp()),
    )

# Run the example
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
