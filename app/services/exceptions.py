"""Custom exceptions for services module."""


class ServiceException(Exception):
    """Base exception for service operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ServiceNotFound(ServiceException):
    """Raised when a service is not found."""

    pass


class ServiceAlreadyExists(ServiceException):
    """Raised when trying to create a service that already exists."""

    pass


class InvalidServiceTypeId(ServiceException):
    """Raised when a service_type_id does not exist."""

    pass
