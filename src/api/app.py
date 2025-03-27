from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from .config import get_api_settings, get_rate_limiter, get_openapi_schema
from .models import ErrorResponse

def create_app() -> tuple[FastAPI, Limiter]:
    settings = get_api_settings()
    
    app = FastAPI(
        title="Accessibility Expert API",
        description="""
        API for accessibility analysis and recommendations.
        
        This API provides endpoints to:
        - Analyze web content for accessibility issues
        - Get expert recommendations for fixing accessibility problems
        - Reference WCAG guidelines and best practices
        """,
        version="1.0.0",
        openapi_url="/openapi.json"  # This is required for the docs to work
    )
    
    # Custom OpenAPI schema
    def custom_openapi():
        app.openapi_schema = get_openapi_schema(app)
        return app.openapi_schema

    app.openapi = custom_openapi
    
    # Rate limiting setup
    limiter = get_rate_limiter()
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],  # Allow all headers for OpenAPI docs
    )

    # Global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error", "type": str(type(exc).__name__)},
        )

    return app, limiter 