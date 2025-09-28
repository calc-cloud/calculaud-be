"""Mock authentication for testing purposes."""

from app.auth.schemas import TokenInfo, User
from app.config import settings


def mock_auth_dependency() -> TokenInfo:
    """Mock authentication dependency that returns a test user."""
    # Create a mock user with admin privileges for testing
    test_user = User(
        sub="test-user-123",
        email="test@example.com",
        username="testuser",
        roles=[settings.admin_role, settings.user_role],
        given_name="Test",
        family_name="User",
    )

    # Create mock token info
    mock_claims = {
        "sub": "test-user-123",
        "email": "test@example.com",
        "preferred_username": "testuser",
        "roles": [settings.admin_role, settings.user_role],
        "given_name": "Test",
        "family_name": "User",
        "iat": 1234567890,
        "exp": 9999999999,  # Far future expiry
        "iss": "test-issuer",
        "aud": "test-audience",
    }

    return TokenInfo(
        raw_token="mock-jwt-token-for-testing", claims=mock_claims, user=test_user
    )


def mock_auth_dependency_no_admin() -> TokenInfo:
    """Mock authentication dependency that returns a regular user (no admin role)."""
    # Create a mock user without admin privileges
    test_user = User(
        sub="test-user-456",
        email="user@example.com",
        username="regularuser",
        roles=[settings.user_role],
        given_name="Regular",
        family_name="User",
    )

    # Create mock token info
    mock_claims = {
        "sub": "test-user-456",
        "email": "user@example.com",
        "preferred_username": "regularuser",
        "roles": [settings.user_role],
        "given_name": "Regular",
        "family_name": "User",
        "iat": 1234567890,
        "exp": 9999999999,  # Far future expiry
        "iss": "test-issuer",
        "aud": "test-audience",
    }

    return TokenInfo(
        raw_token="mock-jwt-token-for-testing", claims=mock_claims, user=test_user
    )
