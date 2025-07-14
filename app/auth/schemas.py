"""Authentication-related models and schemas."""

from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field


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
        user = User(
            sub=claims.get("sub", ""),
            email=claims.get("email"),
            username=claims.get("preferred_username"),
            roles=claims.get("roles", []),
            given_name=claims.get("given_name"),
            family_name=claims.get("family_name"),
        )

        return cls(raw_token=token, claims=claims, user=user)


class TokenRequest(BaseModel):
    """Schema for OAuth token request."""

    grant_type: Annotated[
        Literal["authorization_code"],
        Field(description="OAuth2 grant type - must be 'authorization_code'"),
    ]
    client_id: str
    client_secret: str | None = None
    username: str | None = None
    password: str | None = None
    code: str | None = None
    redirect_uri: str | None = None
    scope: str | None = None
    code_verifier: str | None = None

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
