import asyncio
import signal
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from .analytics.router import router as analytics_router
from .auth.dependencies import require_auth
from .auth.router import router as auth_router
from .config import settings
from .database import get_db
from .files.router import router as files_router
from .health import (
    detailed_health_check,
    liveness_check,
    mark_startup_complete,
    readiness_check,
    startup_check,
)
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

# Global shutdown event
shutdown_event = asyncio.Event()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager for startup and shutdown events.
    """
    # Startup
    mark_startup_complete()

    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        print(f"Received signal {signum}, initiating graceful shutdown...")
        shutdown_event.set()

    # Register signal handlers (SIGTERM is sent by Kubernetes for pod termination)
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    yield

    # Shutdown - wait for shutdown event or timeout
    if shutdown_event.is_set():
        print("Performing graceful shutdown...")

        # Give active requests time to complete
        await asyncio.sleep(2)

        print("Graceful shutdown completed")


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


# Kubernetes health check endpoints
@app.get("/health/live")
def health_live():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if the application is alive, 503 if it should be restarted.
    """
    return liveness_check()


@app.get("/health/ready")
def health_ready(db: Annotated[Session, Depends(get_db)]):
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if the application is ready to serve requests, 503 if not ready.
    """
    return readiness_check(db)


@app.get("/health/startup")
def health_startup():
    """
    Kubernetes startup probe endpoint.
    Returns 200 if the application has started successfully, 503 if still starting.
    """
    return startup_check()


@app.get("/health")
def health_check(db: Annotated[Session, Depends(get_db)]):
    """
    Detailed health check endpoint for monitoring and debugging.
    """
    return detailed_health_check(db)
