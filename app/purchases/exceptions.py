"""Custom exceptions for purchase operations."""


class PurchaseException(Exception):
    """Base exception for purchase operations."""
    
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class PurchaseNotFound(PurchaseException):
    """Exception raised when a purchase is not found."""
    
    def __init__(self, purchase_id: int):
        self.message = f"Purchase with ID {purchase_id} not found"
        super().__init__(self.message)