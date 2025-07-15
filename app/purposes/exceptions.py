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


class FileAttachmentsNotFound(Exception):
    """Raised when a file attachment does not exist."""

    def __init__(self, file_attachment_ids: list[int]):
        self.file_attachment_id = file_attachment_ids
        super().__init__(
            f"File attachment with ID(s) {file_attachment_ids} were not found"
        )


class PurposeNotFound(Exception):
    """Raised when a purpose is not found."""

    def __init__(self, purpose_id: int):
        self.purpose_id = purpose_id
        super().__init__(f"Purpose with ID {purpose_id} not found")


class FileNotAttachedToPurpose(Exception):
    """Raised when a file is not attached to a specific purpose."""

    def __init__(self, file_id: int, purpose_id: int):
        self.file_id = file_id
        self.purpose_id = purpose_id
        super().__init__(
            f"File with ID {file_id} is not attached to purpose with ID {purpose_id}"
        )
