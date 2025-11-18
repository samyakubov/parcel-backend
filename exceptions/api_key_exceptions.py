class MissingApiKeyError(Exception):
    """Exception raised when an API key is missing from the request."""
    pass


class InvalidApiKeyError(Exception):
    """Exception raised when an API key is invalid."""
    pass


class InvalidAdminKeyError(Exception):
    """Exception raised when the admin API key is invalid."""
    pass


class MissingAdminKeyError(Exception):
    """Exception raised when the admin API key is missing."""
    pass


class FailedToCreateApiKeyError(Exception):
    """Exception raised when an API key fails to be created."""
    pass


class FailedToDeleteApiKeyError(Exception):
    """Exception raised when an API key fails to be deleted."""
    pass


class APIKeyNotFoundError(Exception):
    """Exception raised when an API key is not found."""
    pass


class InvalidUpdateError(Exception):
    """Exception raised when an update request is invalid."""
    pass
