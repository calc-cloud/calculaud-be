"""Custom exceptions for suppliers module."""


class SupplierException(Exception):
    """Base exception for supplier operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class SupplierNotFound(SupplierException):
    """Raised when a supplier is not found."""

    pass


class SupplierAlreadyExists(SupplierException):
    """Raised when trying to create a supplier that already exists."""

    pass


class InvalidFileIcon(SupplierException):
    """Raised when file_icon_id refers to a non-existent file."""

    pass
