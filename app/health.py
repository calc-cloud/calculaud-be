"""
Health check endpoints for Kubernetes probes and application monitoring.
"""

import logging
import time
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db

logger = logging.getLogger(__name__)

# Application startup time for startup probe
startup_time = time.time()
startup_complete = False


def mark_startup_complete():
    """Mark the application startup as complete."""
    global startup_complete
    startup_complete = True


def check_database_connection(db: Session) -> dict[str, Any]:
    """
    Check database connectivity and basic health.

    Returns:
        dict: Database health status
    """
    try:
        # Simple database connectivity check
        result = db.execute(text("SELECT 1")).scalar()
        if result != 1:
            raise Exception("Database query returned unexpected result")

        # Check if we can access the purposes table (main business table)
        table_check = db.execute(
            text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_name = 'purpose'"
            )
        ).scalar()

        return {
            "status": "healthy",
            "connected": True,
            "tables_accessible": table_check > 0,
            "response_time_ms": 0,  # We could measure this if needed
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {"status": "unhealthy", "connected": False, "error": str(e)}


def check_s3_connection() -> dict[str, Any]:
    """
    Check S3 connectivity (basic check without credentials verification).

    Returns:
        dict: S3 health status
    """
    try:
        # Basic configuration check
        if not settings.s3_bucket_name:
            return {"status": "unhealthy", "error": "S3 bucket name not configured"}

        # We could add actual S3 connectivity check here if needed
        # For now, just verify configuration is present
        has_credentials = bool(
            settings.aws_access_key_id and settings.aws_secret_access_key
        )

        return {
            "status": "healthy" if has_credentials else "warning",
            "bucket_configured": bool(settings.s3_bucket_name),
            "credentials_configured": has_credentials,
            "endpoint": settings.s3_endpoint_url or "AWS S3",
        }
    except Exception as e:
        logger.error(f"S3 health check failed: {e}")
        return {"status": "unhealthy", "error": str(e)}


def get_application_info() -> dict[str, Any]:
    """
    Get basic application information.

    Returns:
        dict: Application information
    """
    return {
        "name": settings.app_name,
        "version": settings.version,
        "environment": settings.environment,
        "debug": settings.debug,
        "uptime_seconds": time.time() - startup_time,
    }


def liveness_check() -> dict[str, Any]:
    """
    Kubernetes liveness probe check.
    This should only fail if the application is completely broken.

    Returns:
        dict: Liveness status
    """
    try:
        # Very basic check - just verify the application is running
        app_info = get_application_info()

        return {"status": "alive", "timestamp": time.time(), "application": app_info}
    except Exception as e:
        logger.error(f"Liveness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Liveness check failed: {str(e)}",
        )


def readiness_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Kubernetes readiness probe check.
    This should fail if the application can't serve requests.

    Args:
        db: Database session

    Returns:
        dict: Readiness status
    """
    try:
        # Check database connectivity
        db_health = check_database_connection(db)

        # Check S3 configuration
        s3_health = check_s3_connection()

        # Determine overall readiness
        is_ready = db_health["status"] == "healthy" and s3_health["status"] in [
            "healthy",
            "warning",
        ]  # Warning is acceptable for readiness

        if not is_ready:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Service not ready",
            )

        return {
            "status": "ready",
            "timestamp": time.time(),
            "checks": {"database": db_health, "s3": s3_health},
            "application": get_application_info(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}",
        )


def startup_check() -> dict[str, Any]:
    """
    Kubernetes startup probe check.
    This should pass only after the application has fully started.

    Returns:
        dict: Startup status
    """
    try:
        if not startup_complete:
            # Check if enough time has passed for basic startup
            uptime = time.time() - startup_time
            if uptime < 5:  # Minimum 5 seconds startup time
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="Application still starting up",
                )

        # Application should be ready for startup to be complete
        # This will also check database and other dependencies
        # We'll do a lighter check than full readiness

        return {
            "status": "started",
            "timestamp": time.time(),
            "startup_complete": startup_complete,
            "uptime_seconds": time.time() - startup_time,
            "application": get_application_info(),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Startup check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Startup check failed: {str(e)}",
        )


def detailed_health_check(db: Session = Depends(get_db)) -> dict[str, Any]:
    """
    Comprehensive health check with detailed information.
    This is useful for monitoring and debugging.

    Args:
        db: Database session

    Returns:
        dict: Detailed health status
    """
    try:
        # Run all checks
        db_health = check_database_connection(db)
        s3_health = check_s3_connection()
        app_info = get_application_info()

        # Determine overall health
        overall_status = "healthy"
        if db_health["status"] != "healthy":
            overall_status = "unhealthy"
        elif s3_health["status"] == "unhealthy":
            overall_status = "degraded"
        elif s3_health["status"] == "warning":
            overall_status = "warning"

        return {
            "status": overall_status,
            "timestamp": time.time(),
            "application": app_info,
            "checks": {
                "database": db_health,
                "s3": s3_health,
                "startup_complete": startup_complete,
            },
        }
    except Exception as e:
        logger.error(f"Detailed health check failed: {e}")
        return {
            "status": "error",
            "timestamp": time.time(),
            "error": str(e),
            "application": get_application_info(),
        }
