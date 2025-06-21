from fastapi import FastAPI

from .config import settings
from .hierarchies.router import router as hierarchies_router
from .purposes.router import router as purposes_router

app = FastAPI(
    title=settings.app_name,
    description="Backend API for managing procurement purposes, EMFs, costs, and hierarchies",
    version=settings.version,
    debug=settings.debug,
)

# Include routers
app.include_router(
    hierarchies_router,
    prefix=f"{settings.api_v1_prefix}/hierarchies",
    tags=["hierarchies"],
)

app.include_router(
    purposes_router, prefix=f"{settings.api_v1_prefix}/purposes", tags=["purposes"]
)


@app.get("/health")
def health_check():
    """Health check endpoint for deployment platforms like Railway."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }
