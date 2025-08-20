"""
Health check router for Kubernetes probes and application monitoring.
"""

from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..database import get_db
from .checks import (
    detailed_health_check,
    liveness_check,
    readiness_check,
    startup_check,
)

router = APIRouter()


@router.get("/live")
def health_live():
    """
    Kubernetes liveness probe endpoint.
    Returns 200 if the application is alive, 503 if it should be restarted.
    """
    return liveness_check()


@router.get("/ready")
def health_ready(db: Annotated[Session, Depends(get_db)]):
    """
    Kubernetes readiness probe endpoint.
    Returns 200 if the application is ready to serve requests, 503 if not ready.
    """
    return readiness_check(db)


@router.get("/startup")
def health_startup():
    """
    Kubernetes startup probe endpoint.
    Returns 200 if the application has started successfully, 503 if still starting.
    """
    return startup_check()


@router.get("/")
def health_check(db: Annotated[Session, Depends(get_db)]):
    """
    Detailed health check endpoint for monitoring and debugging.
    """
    return detailed_health_check(db)
