from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from slowapi import Limiter
from slowapi.util import get_remote_address
from src.settings.api_settings import APISettings

def get_api_settings() -> APISettings:
    """Get API settings from environment variables"""
    return APISettings()

def get_cors_middleware(settings: APISettings) -> CORSMiddleware:
    """Get CORS middleware configuration"""
    return CORSMiddleware(
        app=None,  # This will be set by FastAPI
        allow_origins=settings.allowed_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "OPTIONS"],
        allow_headers=["*"],  # Allow all headers for OpenAPI docs
    )

def get_rate_limiter() -> Limiter:
    """Get rate limiter configuration"""
    return Limiter(key_func=get_remote_address)

def get_openapi_schema(app: FastAPI) -> dict:
    """Get OpenAPI schema with security configuration"""
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
    
    return openapi_schema
