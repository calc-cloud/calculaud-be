from app.exceptions import NotFoundError, ValidationError


class HierarchyNotFoundError(NotFoundError):
    """Hierarchy not found error."""

    pass


class InvalidHierarchyTypeError(ValidationError):
    """Invalid hierarchy type error."""

    pass


class CircularHierarchyError(ValidationError):
    """Circular hierarchy reference error."""

    pass
