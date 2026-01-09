import logging

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse
from starlette import status

from database_connector import DatabaseError
from exceptions.api_key_exceptions import (
    APIKeyNotFoundError,
    FailedToCreateApiKeyError,
    FailedToDeleteApiKeyError,
    InvalidAdminKeyError,
    InvalidApiKeyError,
    InvalidUpdateError,
    MissingAdminKeyError,
    MissingApiKeyError,
)
from exceptions.geolocation_exceptions import (
    AddressNotInNewYorkError,
    GeolocationError,
)
from exceptions.party_search_exceptions import (
    InvalidPartyNameError,
    PartyNotFoundError,
)
from exceptions.property_search_exceptions import (
    AddressNotFoundError,
    BBLNotFoundError,
    InvalidAddressError,
    InvalidBBLError,
)

logger = logging.getLogger(__name__)

# Map exception types to their HTTP status codes and log levels
EXCEPTION_CONFIG = {
    # 400 Bad Request - Client errors
    InvalidBBLError: (status.HTTP_400_BAD_REQUEST, "warning"),
    InvalidAddressError: (status.HTTP_400_BAD_REQUEST, "warning"),
    InvalidUpdateError: (status.HTTP_400_BAD_REQUEST, "warning"),
    AddressNotInNewYorkError: (status.HTTP_400_BAD_REQUEST, "warning"),
    InvalidPartyNameError: (status.HTTP_400_BAD_REQUEST, "warning"),

    # 401 Unauthorized - Authentication errors
    MissingApiKeyError: (status.HTTP_401_UNAUTHORIZED, "warning"),
    InvalidApiKeyError: (status.HTTP_401_UNAUTHORIZED, "warning"),

    # 403 Forbidden - Authorization errors
    InvalidAdminKeyError: (status.HTTP_403_FORBIDDEN, "warning"),

    # 404 Not Found - Resource not found
    BBLNotFoundError: (status.HTTP_404_NOT_FOUND, "warning"),
    AddressNotFoundError: (status.HTTP_404_NOT_FOUND, "warning"),
    APIKeyNotFoundError: (status.HTTP_404_NOT_FOUND, "warning"),
    PartyNotFoundError: (status.HTTP_404_NOT_FOUND, "warning"),

    # 500 Internal Server Error - Server errors
    MissingAdminKeyError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "error"),
    FailedToCreateApiKeyError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "error"),
    FailedToDeleteApiKeyError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "error"),
    DatabaseError: (status.HTTP_500_INTERNAL_SERVER_ERROR, "error"),

    # 503 Service Unavailable - External service errors
    GeolocationError: (status.HTTP_503_SERVICE_UNAVAILABLE, "error"),
}


def register_exception_handlers(app) -> None:
    """Registers exception handlers for the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handles any unhandled exceptions."""
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "An unexpected error occurred."}
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handles HTTPExceptions."""
        logger.warning(f"HTTPException: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})

    def create_handler(exc_type, code, level):
        async def handler(request: Request, exc: Exception) -> JSONResponse:
            log_func = getattr(logger, level)
            log_func(f"{exc_type.__name__}: {exc}")

            # Use generic message for DatabaseError to avoid exposing internals
            message = "A database error occurred" if exc_type == DatabaseError else str(exc)

            return JSONResponse(status_code=code, content={"message": message})
        return handler

    for exc_class, (status_code, log_level) in EXCEPTION_CONFIG.items():
        app.add_exception_handler(exc_class, create_handler(exc_class, status_code, log_level))
