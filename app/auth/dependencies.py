"""Authentication dependencies for FastAPI routes."""

from typing import Annotated

from fastapi import Depends, HTTPException, Security
from starlette.status import HTTP_403_FORBIDDEN

from .roles import RoleHierarchy
from .schemas import TokenInfo, User
from .security import openid_connect


def require_auth(
    token_info: Annotated[TokenInfo, Security(openid_connect)],
) -> TokenInfo:
    """
    Require authentication and valid user role for endpoint access.

    Args:
        token_info: Validated token information from OpenID Connect

    Returns:
        TokenInfo: Validated token information

    Raises:
        HTTPException: When user doesn't have valid user access
    """
    if not RoleHierarchy.has_user_access(token_info.user.roles):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Valid user role required for this operation",
        )

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


def require_admin(
    token_info: Annotated[TokenInfo, Depends(require_auth)],
) -> TokenInfo:
    """
    Require admin role for endpoint access.

    Args:
        token_info: Validated token information from OpenID Connect

    Returns:
        TokenInfo: Validated token information

    Raises:
        HTTPException: When user doesn't have admin privileges
    """
    if not RoleHierarchy.has_admin_access(token_info.user.roles):
        raise HTTPException(
            status_code=HTTP_403_FORBIDDEN,
            detail="Admin role required for this operation",
        )

    return token_info
