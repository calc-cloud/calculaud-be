class ServiceTypeNotFound(Exception):
    """Raised when a service type is not found."""
    pass


class ServiceTypeAlreadyExists(Exception):
    """Raised when trying to create a service type that already exists."""
    pass
