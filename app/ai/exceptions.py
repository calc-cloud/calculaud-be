class AIException(Exception):
    def __init__(self, message: str):
        self.message = message
        super().__init__(self.message)


class OpenAIError(AIException):
    def __init__(self, message: str):
        self.message = f"OpenAI API error: {message}"
        super().__init__(self.message)


class InvalidRequest(AIException):
    def __init__(self, message: str):
        self.message = f"Invalid request: {message}"
        super().__init__(self.message)
