class MissingApiKeyException(Exception):
    """Exception raised when an API key is missing from the request."""
    def __init__(self):
        super().__init__("Missing API key")

class InvalidApiKeyException(Exception):
    """Exception raised when an API key is invalid."""
    def __init__(self):
        super().__init__("Invalid API key")

class InvalidAdminKeyException(Exception):
    """Exception raised when the admin API key is invalid."""
    def __init__(self):
        super().__init__("Invalid Admin key")

class MissingAdminKeyException(Exception):
    """Exception raised when the admin API key is missing."""
    def __init__(self):
        super().__init__("Missing Admin key")

class FailedToCreateApiKeyException(Exception):
    """Exception raised when an API key fails to be created."""
    def __init__(self):
        super().__init__("Failed to create API key")

class FailedToDeleteApiKeyException(Exception):
    """Exception raised when an API key fails to be deleted."""
    def __init__(self):
        super().__init__("Failed to delete API key")