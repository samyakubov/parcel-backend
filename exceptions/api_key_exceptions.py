class MissingApiKeyError(Exception):
    """Exception raised when an API key is missing from the request."""

    def __init__(self):
        super().__init__("Missing API key")


class InvalidApiKeyError(Exception):
    """Exception raised when an API key is invalid."""

    def __init__(self):
        super().__init__("Invalid API key")


class InvalidAdminKeyError(Exception):
    """Exception raised when the admin API key is invalid."""

    def __init__(self):
        super().__init__("Invalid Admin key")


class MissingAdminKeyError(Exception):
    """Exception raised when the admin API key is missing."""

    def __init__(self):
        super().__init__("Missing Admin key")


class FailedToCreateApiKeyError(Exception):
    """Exception raised when an API key fails to be created."""

    def __init__(self):
        super().__init__("Failed to create API key")


class FailedToDeleteApiKeyError(Exception):
    """Exception raised when an API key fails to be deleted."""

    def __init__(self):
        super().__init__("Failed to delete API key")


class APIKeyNotFoundError(Exception):
    """Exception raised when an API key is not found."""

    def __init__(self):
        super().__init__("API key not found")


class InvalidUpdateError(Exception):
    """Exception raised when an update request is invalid."""

    def __init__(self):
        super().__init__("Invalid update request")
