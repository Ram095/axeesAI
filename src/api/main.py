import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.settings.api_settings import APISettings
from .middleware import SecurityHeadersMiddleware, RequestLoggingMiddleware
from .routes import health, accessibility
from .app import create_app
import os

settings = APISettings()
app, limiter = create_app()

# Mount static files
static_dir = os.path.join(os.path.dirname(__file__), "static")
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Add middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(RequestLoggingMiddleware)

# Include routers
app.include_router(health.router)
app.include_router(accessibility.router)

def start():
    """Start the FastAPI application with uvicorn"""
    uvicorn.run(
        "src.api.main:app",
        host=settings.host,
        port=settings.port,
        reload=False
    )


if __name__ == "__main__":
    start()