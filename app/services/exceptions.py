class ServiceAlreadyExists(Exception):
    """Raised when trying to create a service that already exists."""

    pass


class InvalidServiceTypeId(Exception):
    """Raised when a service_type_id does not exist."""

    pass
