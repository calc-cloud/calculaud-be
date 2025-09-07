"""Custom exceptions for budget sources module."""


class BudgetSourceException(Exception):
    """Base exception for budget source operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class BudgetSourceNotFound(BudgetSourceException):
    """Raised when a budget source is not found."""

    pass


class BudgetSourceAlreadyExists(BudgetSourceException):
    """Raised when trying to create a budget source that already exists."""

    pass
