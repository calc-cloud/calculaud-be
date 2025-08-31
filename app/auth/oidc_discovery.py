"""OIDC Discovery service for auto-discovering authentication endpoints."""

import logging
import ssl
from typing import Any

import requests
from cachetools import TTLCache
from fastapi import HTTPException
from starlette.status import HTTP_503_SERVICE_UNAVAILABLE

from app.config import settings

logger = logging.getLogger(__name__)

# SSL configuration for discovery requests
ssl._create_default_https_context = ssl._create_unverified_context


class OIDCDiscoveryError(Exception):
    """Exception raised when OIDC discovery fails."""

    def __init__(self, message: str, original_error: Exception | None = None):
        self.message = message
        self.original_error = original_error
        super().__init__(self.message)


class OIDCDiscoveryService:
    """Service for discovering OIDC endpoints from .well-known/openid-configuration."""

    def __init__(self, oidc_url: str, ttl_seconds: int = 3600):
        """
        Initialize OIDC discovery service.

        Args:
            oidc_url: The OIDC discovery URL (.well-known/openid-configuration)
            ttl_seconds: How long to cache discovery results (default: 1 hour)
        """
        self.oidc_url = oidc_url
        self._cache: TTLCache = TTLCache(maxsize=1, ttl=ttl_seconds)

    def _fetch_discovery_document(self) -> dict[str, Any]:
        """
        Fetch the OIDC discovery document from the provider.

        Returns:
            dict: The parsed discovery document

        Raises:
            OIDCDiscoveryError: When discovery fails or document is invalid
        """
        try:
            logger.info(f"Fetching OIDC discovery document from {self.oidc_url}")

            response = requests.get(
                self.oidc_url,
                timeout=30.0,
                verify=False,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "calculaud-be/1.0.0",
                },
            )
            response.raise_for_status()

            discovery_doc = response.json()

            # Validate required fields are present
            required_fields = ["issuer", "jwks_uri", "token_endpoint"]
            missing_fields = [
                field for field in required_fields if field not in discovery_doc
            ]

            if missing_fields:
                raise OIDCDiscoveryError(
                    f"Discovery document missing required fields: {', '.join(missing_fields)}"
                )

            logger.info("Successfully fetched OIDC discovery document")
            return discovery_doc

        except requests.exceptions.RequestException as e:
            error_msg = f"Failed to fetch OIDC discovery document from {self.oidc_url}"
            logger.error(f"{error_msg}: {str(e)}")
            raise OIDCDiscoveryError(error_msg, e)

        except ValueError as e:
            error_msg = f"Invalid JSON in OIDC discovery document from {self.oidc_url}"
            logger.error(f"{error_msg}: {str(e)}")
            raise OIDCDiscoveryError(error_msg, e)

    def get_discovery_document(self, force_refresh: bool = False) -> dict[str, Any]:
        """
        Get the OIDC discovery document, using cache if available.

        Args:
            force_refresh: Force a fresh fetch even if cache is valid

        Returns:
            dict: The OIDC discovery document

        Raises:
            OIDCDiscoveryError: When discovery fails
        """
        if force_refresh:
            self._cache.clear()

        if "document" not in self._cache:
            self._cache["document"] = self._fetch_discovery_document()

        return self._cache["document"]

    def get_jwks_uri(self) -> str:
        """
        Get the JWKS URI from discovery document.

        Returns:
            str: The JWKS URI

        Raises:
            OIDCDiscoveryError: When discovery fails
        """
        doc = self.get_discovery_document()
        return doc["jwks_uri"]

    def get_issuer(self) -> str:
        """
        Get the issuer from discovery document.

        Returns:
            str: The issuer URI

        Raises:
            OIDCDiscoveryError: When discovery fails
        """
        doc = self.get_discovery_document()
        return doc["issuer"]

    def get_token_endpoint(self) -> str:
        """
        Get the token endpoint from discovery document.

        Returns:
            str: The token endpoint URI

        Raises:
            OIDCDiscoveryError: When discovery fails
        """
        doc = self.get_discovery_document()
        return doc["token_endpoint"]

    def get_supported_algorithms(self) -> list[str]:
        """
        Get supported signing algorithms from discovery document.

        Returns:
            list[str]: List of supported algorithms

        Raises:
            OIDCDiscoveryError: When discovery fails or algorithms not available
        """
        doc = self.get_discovery_document()
        algorithms = doc.get("id_token_signing_alg_values_supported")

        if not algorithms:
            raise OIDCDiscoveryError(
                "OIDC discovery document does not specify supported signing algorithms "
                "(id_token_signing_alg_values_supported)"
            )

        return algorithms

    def health_check(self) -> dict[str, Any]:
        """
        Perform a health check on the OIDC discovery service.

        Returns:
            dict: Health check results
        """
        try:
            # Try to fetch discovery document (will use cache if available)
            doc = self.get_discovery_document()

            return {
                "status": "healthy",
                "oidc_url": self.oidc_url,
                "issuer": doc.get("issuer"),
                "cache_info": {
                    "maxsize": self._cache.maxsize,
                    "currsize": self._cache.currsize,
                    "ttl": self._cache.ttl,
                    "cached": "document" in self._cache,
                },
            }

        except OIDCDiscoveryError as e:
            return {
                "status": "unhealthy",
                "oidc_url": self.oidc_url,
                "error": e.message,
                "cache_info": {
                    "maxsize": self._cache.maxsize,
                    "currsize": self._cache.currsize,
                    "ttl": self._cache.ttl,
                    "cached": False,
                },
            }


def validate_discovery_service_or_raise_http_exception(
    service: OIDCDiscoveryService,
) -> None:
    """
    Validate that the discovery service is working, raise HTTPException if not.

    Args:
        service: The OIDC discovery service to validate

    Raises:
        HTTPException: 503 Service Unavailable if discovery is failing
    """
    health = service.health_check()
    if health["status"] != "healthy":
        raise HTTPException(
            status_code=HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"OIDC discovery service unavailable: {health.get('error', 'Unknown error')}",
        )


# Global OIDC discovery service instance - shared across the auth module
oidc_discovery_service = OIDCDiscoveryService(settings.auth_oidc_url)
