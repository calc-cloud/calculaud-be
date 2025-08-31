"""Authentication-related models and schemas."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field

from app.config import settings


def extract_roles_from_claims(claims: dict, claim_path: str) -> list[str]:
    """
    Extract roles from JWT claims using a configurable claim path.

    Supports nested claim paths like "cognito:groups" and handles both
    string and array role formats.

    Args:
        claims: JWT token claims dictionary
        claim_path: Dot or colon-separated path to the roles claim

    Returns:
        list[str]: List of extracted roles
    """
    # Handle nested claim paths (support both "." and ":" separators)
    path_parts = claim_path.replace(":", ".").split(".")

    # Navigate to the nested claim
    current_value = claims
    for part in path_parts:
        if isinstance(current_value, dict) and part in current_value:
            current_value = current_value[part]
        else:
            return []

    # Handle both string and array formats
    if isinstance(current_value, str):
        return [current_value]
    elif isinstance(current_value, list):
        # Ensure all items are strings
        return [str(role) for role in current_value if role]

    return []


class User(BaseModel):
    """User model representing authenticated user from JWT token."""

    sub: Annotated[str, Field(description="Subject (user ID) from token")]
    email: Annotated[str | None, Field(default=None, description="User email")]
    username: Annotated[str | None, Field(default=None, description="Username")]
    roles: Annotated[
        list[str], Field(default_factory=list, description="User roles/scopes")
    ]
    given_name: Annotated[
        str | None, Field(default=None, description="User's first name")
    ]
    family_name: Annotated[
        str | None, Field(default=None, description="User's last name")
    ]

    @property
    def full_name(self) -> str | None:
        """Get user's full name if available."""
        if self.given_name and self.family_name:
            return f"{self.given_name} {self.family_name}"
        return self.given_name or self.family_name

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def has_any_role(self, roles: list[str]) -> bool:
        """Check if user has any of the specified roles."""
        return any(role in self.roles for role in roles)

    def has_all_roles(self, roles: list[str]) -> bool:
        """Check if user has all of the specified roles."""
        return all(role in self.roles for role in roles)


class TokenInfo(BaseModel):
    """Information extracted from JWT token."""

    raw_token: Annotated[str, Field(description="Original JWT token")]
    claims: Annotated[dict, Field(description="All token claims")]
    user: Annotated[User, Field(description="User information")]

    @classmethod
    def from_token_claims(cls, token: str, claims: dict) -> "TokenInfo":
        """Create TokenInfo from JWT token and claims."""
        # Extract roles using configurable claim path
        roles = extract_roles_from_claims(claims, settings.role_claim_path)

        user = User(
            sub=claims.get("sub", ""),
            email=claims.get("email"),
            username=claims.get("preferred_username"),
            roles=roles,
            given_name=claims.get("given_name"),
            family_name=claims.get("family_name"),
        )

        return cls(raw_token=token, claims=claims, user=user)


class TokenRequest(BaseModel):
    """Schema for OAuth token request."""

    grant_type: Annotated[
        Literal["authorization_code", "refresh_token"],
        Field(
            description="OAuth2 grant type - 'authorization_code' or 'refresh_token'"
        ),
    ]
    client_id: str
    client_secret: str | None = None
    username: str | None = None
    password: str | None = None
    code: str | None = None
    redirect_uri: str | None = None
    scope: str | None = None
    code_verifier: str | None = None
    refresh_token: str | None = None

    model_config = ConfigDict(extra="allow")


class TokenResponse(BaseModel):
    """Schema for OAuth token response."""

    access_token: str | None = None
    token_type: str | None = None
    expires_in: int | None = None
    refresh_token: str | None = None
    id_token: str | None = None
    scope: str | None = None
    error: str | None = None
    error_description: str | None = None

    model_config = ConfigDict(extra="allow")
