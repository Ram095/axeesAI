from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from src.settings import APISettings

from .api_settings import APISettings
from .middleware import SecurityHeadersMiddleware

def create_app() -> tuple[FastAPI, Limiter]:
    settings = APISettings()
    
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
        docs_url=None,  # We'll serve these manually
        redoc_url=None,  # We'll serve these manually
        openapi_url="/openapi.json"  # This is required for the docs to work
    )
    
    # Custom OpenAPI schema
    def custom_openapi():
        if app.openapi_schema:
            return app.openapi_schema
        openapi_schema = get_openapi(
            title=app.title,
            version=app.version,
            description=app.description,
            routes=app.routes,
        )
        # Add security schemes
        openapi_schema["components"] = {
            "securitySchemes": {
                "ApiKeyHeader": {
                    "type": "apiKey",
                    "in": "header",
                    "name": "X-Open-API-Key"
                }
            }
        }
        openapi_schema["security"] = [{"ApiKeyHeader": []}]
        app.openapi_schema = openapi_schema
        return app.openapi_schema

    app.openapi = custom_openapi
    
    # Rate limiting setup
    limiter = Limiter(key_func=get_remote_address)
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # Add CORS middleware with configurable origins
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

settings = APISettings()
