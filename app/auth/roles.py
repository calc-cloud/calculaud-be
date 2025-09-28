"""Role management system for the Procurement Management System."""

from enum import Enum

from app.config import settings


class RoleEnum(str, Enum):
    """Enumeration of available user roles."""

    ADMIN = settings.admin_role
    USER = settings.user_role

    def __str__(self) -> str:
        """Return the string value of the role."""
        return self.value


class RoleHierarchy:
    """Manages role hierarchy and permissions."""

    # Role hierarchy: higher-level roles include permissions of lower-level roles
    HIERARCHY = {
        RoleEnum.ADMIN: [RoleEnum.ADMIN, RoleEnum.USER],
        RoleEnum.USER: [RoleEnum.USER],
    }

    @classmethod
    def can_access(cls, user_roles: list[str], required_role: RoleEnum) -> bool:
        """
        Check if user roles provide access to the required role level.

        Args:
            user_roles: List of user's roles
            required_role: Required role for access

        Returns:
            bool: True if user has sufficient access
        """
        for user_role in user_roles:
            try:
                role_enum = RoleEnum(user_role)
                if required_role in cls.HIERARCHY.get(role_enum, []):
                    return True
            except ValueError:
                # Skip invalid roles
                continue
        return False

    @classmethod
    def has_admin_access(cls, user_roles: list[str]) -> bool:
        """
        Check if user has admin access.

        Args:
            user_roles: List of user's roles

        Returns:
            bool: True if user has admin access
        """
        return cls.can_access(user_roles, RoleEnum.ADMIN)

    @classmethod
    def has_user_access(cls, user_roles: list[str]) -> bool:
        """
        Check if user has at least user access.

        Args:
            user_roles: List of user's roles

        Returns:
            bool: True if user has user access or higher
        """
        return cls.can_access(user_roles, RoleEnum.USER)
