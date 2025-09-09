"""Authentication dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, Security
from starlette.status import HTTP_403_FORBIDDEN

from app.config import settings

from .schemas import TokenInfo, User
from .security import openid_connect


def require_auth(
    token_info: Annotated[TokenInfo, Security(openid_connect)],
) -> TokenInfo:
    """
    Require authentication for endpoint access.

    Args:
        token_info: Validated token information from OpenID Connect

    Returns:
        TokenInfo: Validated token information
    """
    return token_info


def get_current_user(token_info: Annotated[TokenInfo, Depends(require_auth)]) -> User:
    """
    Get the current authenticated user.

    Args:
        token_info: Validated token information

    Returns:
        User: Current authenticated user
    """
    return token_info.user


def require_roles(*required_roles: str):
    """
    Create a dependency that requires specific roles.

    Args:
        *required_roles: Variable number of required roles

    Returns:
        Function: Dependency function that validates roles
    """

    def role_dependency(
        token_info: Annotated[TokenInfo, Depends(require_auth)],
    ) -> TokenInfo:
        if not token_info.user.has_any_role(list(required_roles)):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"Required roles: {', '.join(required_roles)}",
            )

        return token_info

    return role_dependency


def require_all_roles(*required_roles: str):
    """
    Create a dependency that requires ALL specified roles.

    Args:
        *required_roles: Variable number of required roles (all must be present)

    Returns:
        Function: Dependency function that validates all roles are present
    """

    def role_dependency(
        token_info: Annotated[TokenInfo, Depends(require_auth)],
    ) -> TokenInfo:
        if not token_info.user.has_all_roles(list(required_roles)):
            raise HTTPException(
                status_code=HTTP_403_FORBIDDEN,
                detail=f"All required roles must be present: {', '.join(required_roles)}",
            )

        return token_info

    return role_dependency


# Common role-based dependencies
require_user = require_roles(settings.required_role)
