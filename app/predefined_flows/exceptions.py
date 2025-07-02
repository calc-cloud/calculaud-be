"""Custom exceptions for predefined flows module."""


class PredefinedFlowException(Exception):
    """Base exception for predefined flow operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class PredefinedFlowNotFound(PredefinedFlowException):
    """Raised when a predefined flow is not found."""

    def __init__(self, flow_id: int):
        self.message = f"Predefined flow with ID {flow_id} not found"
        super().__init__(self.message)


class PredefinedFlowAlreadyExists(PredefinedFlowException):
    """Raised when trying to create a predefined flow that already exists."""

    def __init__(self, flow_name: str):
        self.message = f"Predefined flow '{flow_name}' already exists"
        super().__init__(self.message)


class InvalidStageTypeId(PredefinedFlowException):
    """Raised when referencing a stage type that doesn't exist."""

    def __init__(self, stage_type_id: int):
        self.message = f"Stage type with ID {stage_type_id} not found"
        super().__init__(self.message)