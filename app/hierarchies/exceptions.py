"""Custom exceptions for hierarchies module."""


class HierarchyException(Exception):
    """Base exception for hierarchy operations."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class HierarchyNotFound(HierarchyException):
    """Exception raised when a hierarchy is not found."""

    def __init__(self, hierarchy_id: int):
        super().__init__(f"Hierarchy with id {hierarchy_id} not found")
        self.hierarchy_id = hierarchy_id


class ParentHierarchyNotFound(HierarchyException):
    """Exception raised when a parent hierarchy is not found."""

    def __init__(self, parent_id: int):
        super().__init__(f"Parent hierarchy with id {parent_id} not found")
        self.parent_id = parent_id


class DuplicateHierarchyName(HierarchyException):
    """Exception raised when trying to create a hierarchy with duplicate name under same parent."""

    def __init__(self, name: str):
        super().__init__(
            f"Hierarchy with name '{name}' already exists under the same parent"
        )
        self.name = name


class CircularReferenceError(HierarchyException):
    """Exception raised when a circular reference would be created."""

    def __init__(
        self, message: str = "This parent assignment would create a circular reference"
    ):
        super().__init__(message)


class SelfParentError(HierarchyException):
    """Exception raised when trying to set a hierarchy as its own parent."""

    def __init__(self):
        super().__init__("A hierarchy cannot be its own parent")


class HierarchyHasChildren(HierarchyException):
    """Exception raised when trying to delete a hierarchy that has children."""

    def __init__(self, children_count: int):
        super().__init__(
            f"Cannot delete hierarchy with {children_count} children. Please delete children first."
        )
        self.children_count = children_count


class HierarchyHasPurposes(HierarchyException):
    """Exception raised when trying to delete a hierarchy that has associated purposes."""

    def __init__(self, purposes_count: int):
        super().__init__(
            f"Cannot delete hierarchy with {purposes_count} associated purposes. Reassign purposes first."
        )
        self.purposes_count = purposes_count
