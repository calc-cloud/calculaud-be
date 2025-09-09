from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .analytics.router import router as analytics_router
from .auth.dependencies import require_auth
from .auth.router import router as auth_router
from .config import settings
from .files.router import router as files_router
from .health import mark_startup_complete
from .health.router import router as health_router
from .hierarchies.router import router as hierarchies_router
from .predefined_flows.router import router as predefined_flows_router
from .purchases.router import router as purchases_router
from .purposes.router import router as purposes_router
from .responsible_authorities.router import router as responsible_authorities_router
from .service_types.router import router as service_types_router
from .services.router import router as services_router
from .stage_types.router import router as stage_types_router
from .stages.router import router as stages_router
from .suppliers.router import router as suppliers_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    mark_startup_complete()

    yield

    # Shutdown - let uvicorn handle graceful shutdown
    print("Application shutdown complete")


# Swagger UI OAuth configuration
swagger_ui_init_oauth = {
    "clientId": settings.oauth_client_id,
    "scopes": settings.oauth_scopes.split(),
    "appName": settings.app_name,
}

app = FastAPI(
    title=settings.app_name,
    description="Backend API for managing procurement purposes, purchases, costs, hierarchies,"
    " service types, services, and suppliers",
    version=settings.version,
    debug=settings.debug,
    swagger_ui_init_oauth=swagger_ui_init_oauth,
    lifespan=lifespan,
    root_path=settings.root_path,  # Enable reverse proxy path prefix support
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Common authentication dependency for all protected routes
protected_dependencies = [Depends(require_auth)]

# Include auth router - no authentication required for proxy endpoints
app.include_router(
    auth_router,
    prefix=f"{settings.api_v1_prefix}/auth",
    tags=["auth"],
)

# Include health router - no authentication required for health checks
app.include_router(
    health_router,
    prefix="/health",
    tags=["health"],
)

# Include routers - all protected by authentication
app.include_router(
    hierarchies_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/hierarchies",
    tags=["hierarchies"],
)

app.include_router(
    predefined_flows_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/predefined-flows",
    tags=["predefined-flows"],
)

app.include_router(
    purposes_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/purposes",
    tags=["purposes"],
)

app.include_router(
    service_types_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/service-types",
    tags=["service-types"],
)

app.include_router(
    services_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/services",
    tags=["services"],
)

app.include_router(
    responsible_authorities_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/responsible-authorities",
    tags=["responsible-authorities"],
)

app.include_router(
    stage_types_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/stage-types",
    tags=["stage-types"],
)

app.include_router(
    stages_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/stages",
    tags=["stages"],
)

app.include_router(
    suppliers_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/suppliers",
    tags=["suppliers"],
)

app.include_router(
    files_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/files",
    tags=["files"],
)

app.include_router(
    purchases_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/purchases",
    tags=["purchases"],
)

app.include_router(
    analytics_router,
    dependencies=protected_dependencies,
    prefix=f"{settings.api_v1_prefix}/analytics",
    tags=["analytics"],
)


@app.get("/")
def root():
    return {"message": settings.app_name, "version": settings.version}
