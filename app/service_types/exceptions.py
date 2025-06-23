"""Custom exceptions for service types module."""


class ServiceTypeException(Exception):
    """Base exception for service type operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ServiceTypeNotFound(ServiceTypeException):
    """Raised when a service type is not found."""

    pass


class ServiceTypeAlreadyExists(ServiceTypeException):
    """Raised when trying to create a service type that already exists."""

    pass
