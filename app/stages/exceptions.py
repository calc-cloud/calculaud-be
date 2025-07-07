"""Custom exceptions for stage operations."""


class StageException(Exception):
    """Base exception for stage operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class StageNotFound(StageException):
    """Exception raised when a stage is not found."""

    def __init__(self, stage_id: int):
        self.message = f"Stage with ID {stage_id} not found"
        super().__init__(self.message)


class InvalidStageValue(StageException):
    """Exception raised when stage value doesn't meet requirements."""

    def __init__(self, stage_type_name: str, reason: str):
        self.message = f"Invalid value for stage type '{stage_type_name}': {reason}"
        super().__init__(self.message)
