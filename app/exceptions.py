class BaseAppException(Exception):
    """Base application exception."""

    pass


class NotFoundError(BaseAppException):
    """Resource not found error."""

    pass


class ValidationError(BaseAppException):
    """Validation error."""

    pass


class DatabaseError(BaseAppException):
    """Database operation error."""

    pass
