import logging
from contextlib import asynccontextmanager
from typing import Any, Dict, Optional, Set

import fastapi_mcp
from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi_mcp import FastApiMCP

from app.auth.dependencies import require_auth

from .analytics.router import router as analytics_router
from .auth.router import router as auth_router
from .config import settings
from .files.router import router as files_router
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

logger = logging.getLogger(__name__)


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
# protected_dependencies = []
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


@app.get("/health")
def health_check():
    """Health check endpoint for deployment platforms like Railway."""
    return {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
    }


def resolve_schema_references(
    schema_part: Dict[str, Any],
    reference_schema: Dict[str, Any],
    seen: Optional[Set[str]] = None,
) -> Dict[str, Any]:
    """
    Resolve schema references in OpenAPI schemas.

    Args:
        schema_part: The part of the schema being processed that may contain references
        reference_schema: The complete schema used to resolve references from
        seen: A set of already seen references to avoid infinite recursion

    Returns:
        The schema with references resolved
    """
    seen = seen or set()

    # Make a copy to avoid modifying the input schema
    schema_part = schema_part.copy()

    # Handle $ref directly in the schema
    if "$ref" in schema_part:
        ref_path = schema_part["$ref"]
        # Standard OpenAPI references are in the format "#/components/schemas/ModelName"
        if ref_path.startswith("#/components/schemas/"):
            if ref_path in seen:
                return {"$ref": ref_path}
            seen.add(ref_path)
            model_name = ref_path.split("/")[-1]
            if (
                "components" in reference_schema
                and "schemas" in reference_schema["components"]
            ):
                if model_name in reference_schema["components"]["schemas"]:
                    # Replace with the resolved schema
                    ref_schema = reference_schema["components"]["schemas"][
                        model_name
                    ].copy()
                    # Remove the $ref key and merge with the original schema
                    schema_part.pop("$ref")
                    schema_part.update(ref_schema)

    # Recursively resolve references in all dictionary values
    for key, value in schema_part.items():
        if isinstance(value, dict):
            schema_part[key] = resolve_schema_references(value, reference_schema, seen)
        elif isinstance(value, list):
            # Only process list items that are dictionaries since only they can contain refs
            schema_part[key] = [
                (
                    resolve_schema_references(item, reference_schema, seen)
                    if isinstance(item, dict)
                    else item
                )
                for item in value
            ]

    return schema_part


fastapi_mcp.openapi.utils.resolve_schema_references = resolve_schema_references

# FastMCP Integration - Create MCP server from FastAPI app
logger.info("Setting up FastMCP server")

try:
    mcp = FastApiMCP(
        app,
        name="Calculaud MCP",
        description="MCP Server For Calculaud",
        describe_all_responses=True,
        describe_full_response_schema=True,
        include_operations=["get_suppliers"],
    )

    # Mount the MCP server directly to your app
    mcp.mount_http()

    logger.info(
        "FastMCP server mounted at /mcp - endpoints auto-discovered as MCP tools"
    )
except Exception as e:
    print(e)
