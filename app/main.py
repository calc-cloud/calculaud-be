from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .hierarchies.router import router as hierarchies_router
from .purposes.router import router as purposes_router
from .service_types.router import router as service_types_router
from .suppliers.router import router as suppliers_router

app = FastAPI(
    title=settings.app_name,
    description="Backend API for managing procurement purposes, EMFs, costs, hierarchies, service types, and suppliers",
    version=settings.version,
    debug=settings.debug,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

app.include_router(
    service_types_router,
    prefix=f"{settings.api_v1_prefix}/service-types",
    tags=["service-types"],
)

app.include_router(
    suppliers_router,
    prefix=f"{settings.api_v1_prefix}/suppliers",
    tags=["suppliers"],
)


@app.get("/")
def root():
    return {"message": settings.app_name, "version": settings.version}


@app.get("/health")
def health_check():
    """Health check endpoint for deployment platforms like Railway."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }
