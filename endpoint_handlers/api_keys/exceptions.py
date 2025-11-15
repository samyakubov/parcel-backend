class MissingApiKeyException(Exception):
    def __init__(self):
        super().__init__("Missing API key")

class InvalidApiKeyException(Exception):
    def __init__(self):
        super().__init__("Invalid API key")

class InvalidAdminKeyException(Exception):
    def __init__(self):
        super().__init__("Invalid Admin key")

class MissingAdminKeyException(Exception):
    def __init__(self):
        super().__init__("Missing Admin key")

class FailedToCreateApiKeyException(Exception):
    def __init__(self):
        super().__init__("Failed to create API key")

class FailedToDeleteApiKeyException(Exception):
    def __init__(self):
        super().__init__("Failed to delete API key")