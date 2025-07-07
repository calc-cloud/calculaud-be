from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .analytics.router import router as analytics_router
from .config import settings
from .files.router import router as files_router
from .hierarchies.router import router as hierarchies_router
from .predefined_flows.router import router as predefined_flows_router
from .purchases.router import router as purchases_router
from .purposes.router import router as purposes_router
from .service_types.router import router as service_types_router
from .services.router import router as services_router
from .stage_types.router import router as stage_types_router
from .suppliers.router import router as suppliers_router

app = FastAPI(
    title=settings.app_name,
    description="Backend API for managing procurement purposes, EMFs, costs, hierarchies,"
    " service types, services, and suppliers",
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
    predefined_flows_router,
    prefix=f"{settings.api_v1_prefix}/predefined-flows",
    tags=["predefined-flows"],
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
    services_router,
    prefix=f"{settings.api_v1_prefix}/services",
    tags=["services"],
)

app.include_router(
    stage_types_router,
    prefix=f"{settings.api_v1_prefix}/stage-types",
    tags=["stage-types"],
)

app.include_router(
    suppliers_router,
    prefix=f"{settings.api_v1_prefix}/suppliers",
    tags=["suppliers"],
)

app.include_router(
    files_router,
    prefix=f"{settings.api_v1_prefix}/files",
    tags=["files"],
)

app.include_router(
    purchases_router,
    prefix=f"{settings.api_v1_prefix}/purchases",
    tags=["purchases"],
)

app.include_router(
    analytics_router,
    prefix=f"{settings.api_v1_prefix}/analytics",
    tags=["analytics"],
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
