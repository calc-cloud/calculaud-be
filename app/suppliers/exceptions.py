class SupplierNotFound(Exception):
    """Raised when a supplier is not found."""

    pass


class SupplierAlreadyExists(Exception):
    """Raised when trying to create a supplier that already exists."""

    pass
