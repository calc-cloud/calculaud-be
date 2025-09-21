"""OpenID Connect security implementation."""

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

from app.auth.schemas import TokenInfo
from app.config import settings

# SSL configuration for JWKS client
ssl._create_default_https_context = ssl._create_unverified_context

pyjwt = PyJWT()


class OpenIdConnect(SecurityBase):
    """OpenID Connect authentication handler using JWT tokens."""

    def __init__(
        self,
        openid_connect_url: str | None = None,
        jwks_url: str | None = None,
        audience: str | None = None,
        issuer: str | None = None,
        algorithm: str = "RS256",
        scopes_claim: str = "roles",
    ):
        """
        Initialize OpenID Connect authentication.

        Args:
            openid_connect_url: OpenID Connect discovery URL
            jwks_url: JWKS endpoint URL for token verification
            audience: Expected audience in JWT tokens
            issuer: Expected issuer in JWT tokens
            algorithm: JWT signing algorithm (default: RS256)
            scopes_claim: Name of the claim containing user roles/scopes
        """
        # Use provided values or fall back to settings
        self.jwks_url = jwks_url or settings.auth_jwks_url
        self.audience = audience or settings.auth_audience
        self.issuer = issuer or settings.auth_issuer
        self.algorithm = algorithm or settings.auth_algorithm
        self.scopes_claim = scopes_claim

        # Initialize JWKS client
        self.jwks_client = PyJWKClient(self.jwks_url)

        # Create OpenAPI model
        self.model = OpenIdConnectModel(
            openIdConnectUrl=openid_connect_url or settings.auth_oidc_url,
            description=f"OpenID Connect authentication with role-based access control. "
            f"Supports {settings.user_role} (read-only) and {settings.admin_role} (full CRUD) roles.",
        )
        self.scheme_name = "OpenIdConnect"

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
            # Get signing key and decode token
            signing_key = self.jwks_client.get_signing_key_from_jwt(token)
            claims = pyjwt.decode(
                token,
                signing_key.key,
                algorithms=[self.algorithm],
                audience=self.audience if self.audience else None,
                issuer=self.issuer,
            )
        except PyJWTError as e:
            raise HTTPException(
                status_code=HTTP_401_UNAUTHORIZED,
                detail=f"Invalid authentication token: {str(e)}",
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
