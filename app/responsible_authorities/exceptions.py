class ResponsibleAuthorityException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class ResponsibleAuthorityNotFound(ResponsibleAuthorityException):
    def __init__(self, authority_id: int):
        self.message = f"Responsible authority with ID {authority_id} not found"
        super().__init__(self.message)


class ResponsibleAuthorityAlreadyExists(ResponsibleAuthorityException):
    def __init__(self, name: str):
        self.message = f"Responsible authority with name '{name}' already exists"
        super().__init__(self.message)
