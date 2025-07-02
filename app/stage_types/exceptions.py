"""Custom exceptions for stage types module."""


class StageTypeException(Exception):
    """Base exception for stage type operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class StageTypeNotFound(StageTypeException):
    """Raised when a stage type is not found."""

    def __init__(self, stage_type_id: int):
        self.message = f"Stage type with ID {stage_type_id} not found"
        super().__init__(self.message)


class StageTypeAlreadyExists(StageTypeException):
    """Raised when trying to create a stage type that already exists."""

    def __init__(self, name: str):
        self.message = f"Stage type '{name}' already exists"
        super().__init__(self.message)
