"""Purpose-specific exceptions."""


class ServiceNotFound(Exception):
    """Raised when a service is not found."""

    def __init__(self, service_id: int):
        self.service_id = service_id
        super().__init__(f"Service with ID {service_id} does not exist")


class DuplicateServiceInPurpose(Exception):
    """Raised when trying to add a duplicate service to purpose contents."""

    def __init__(self, service_id: int):
        self.service_id = service_id
        super().__init__(
            f"Service with ID {service_id} is already included in this purpose"
        )
