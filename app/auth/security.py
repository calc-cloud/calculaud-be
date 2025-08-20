"""OpenID Connect security implementation."""

import logging
import ssl

from fastapi import HTTPException
from fastapi.openapi.models import OpenIdConnect as OpenIdConnectModel
from fastapi.security import HTTPBearer, SecurityScopes
from fastapi.security.base import SecurityBase
from jwt.api_jwt import PyJWT
from jwt.exceptions import PyJWTError
from jwt.jwks_client import PyJWKClient
from starlette.requests import Request
from starlette.status import HTTP_401_UNAUTHORIZED, HTTP_403_FORBIDDEN

from app.auth.oidc_discovery import oidc_discovery_service
from app.auth.schemas import TokenInfo
from app.config import settings

# SSL configuration for JWKS client
ssl._create_default_https_context = ssl._create_unverified_context

logger = logging.getLogger(__name__)
pyjwt = PyJWT()


class OpenIdConnect(SecurityBase):
    """OpenID Connect authentication handler using JWT tokens with OIDC discovery."""

    def __init__(
        self,
        audience: str | None = None,
        scopes_claim: str = "roles",
    ):
        """
        Initialize OpenID Connect authentication with OIDC discovery.

        Args:
            audience: Expected audience in JWT tokens
            scopes_claim: Name of the claim containing user roles/scopes
        """
        self.oidc_url = oidc_discovery_service.oidc_url

        # Use provided values or fall back to settings
        self.audience = audience or settings.auth_audience
        self.scopes_claim = scopes_claim

        # Lazy initialization for JWKS client only
        self._jwks_client = None

        # Create OpenAPI model
        self.model = OpenIdConnectModel(
            openIdConnectUrl=self.oidc_url,
            description="OpenID Connect authentication with auto-discovery",
        )
        self.scheme_name = "OpenIdConnect"

    @property
    def jwks_client(self) -> PyJWKClient:
        """Lazy initialization of JWKS client."""
        if self._jwks_client is None:
            jwks_url = oidc_discovery_service.get_jwks_uri()
            self._jwks_client = PyJWKClient(jwks_url)
        return self._jwks_client

    async def __call__(
        self, security_scopes: SecurityScopes, request: Request
    ) -> TokenInfo:
        """
        Validate JWT token and return token information.

        Args:
            security_scopes: Required security scopes for the endpoint
            request: HTTP request object

        Returns:
            TokenInfo: Validated token information with user details

        Raises:
            HTTPException: When token is invalid or insufficient permissions
        """
        # Extract bearer token
        bearer = await HTTPBearer()(request)
        token = bearer.credentials if bearer else ""

        if not token:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail="No authentication token provided",
            )

        try:
            # Get discovered issuer
            issuer = oidc_discovery_service.get_issuer()

            # Get signing key and decode token
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            claims = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=oidc_discovery_service.get_supported_algorithms(),
                audience=self.audience if self.audience else None,
                issuer=issuer,
            )
        except PyJWTError as e:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
            ) from e
        except Exception as e:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=f"Token validation failed: {str(e)}",
            ) from e

        # Check required scopes if specified
        if security_scopes.scopes:
            user_scopes = claims.get(self.scopes_claim, [])
            if not set(security_scopes.scopes).issubset(set(user_scopes)):
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required: {', '.join(security_scopes.scopes)}",
                )

        # Create and return token info
        return TokenInfo.from_token_claims(token, claims)


# Create default authentication instance
openid_connect = OpenIdConnect()
