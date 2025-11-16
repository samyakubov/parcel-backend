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
from exceptions.property_search_exceptions import (
    AddressNotFoundError,
    BBLNotFoundError,
    InvalidAddressError,
    InvalidBBLError,
)

logger = logging.getLogger(__name__)


def register_exception_handlers(app) -> None:
    """Registers exception handlers for the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        """Handles any unhandled exceptions.

        Args:
            request (Request): The incoming request.
            exc (Exception): The exception that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and a generic error message.
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "An unexpected error occurred."}
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
        """Handles HTTPExceptions.

        Args:
            request (Request): The incoming request.
            exc (HTTPException): The HTTPException that was raised.

        Returns:
            JSONResponse: A JSON response with the exception's status code and a generic error message.
        """
        logger.warning(f"HTTPException: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"message": exc.detail})

    @app.exception_handler(InvalidBBLError)
    async def invalid_bbl_handler(request: Request, exc: InvalidBBLError) -> JSONResponse:
        """Handles InvalidBBLErrors.

        Args:
            request (Request): The incoming request.
            exc (InvalidBBLError): The InvalidBBLError that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        logger.warning(f"Invalid BBL: {exc}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})

    @app.exception_handler(BBLNotFoundError)
    async def bbl_not_found_handler(request: Request, exc: BBLNotFoundError) -> JSONResponse:
        """Handles BBLNotFoundErrors.

        Args:
            request (Request): The incoming request.
            exc (BBLNotFoundError): The BBLNotFoundError that was raised.

        Returns:
            JSONResponse: A JSON response with a 404 status code and the exception's message.
        """
        logger.warning(f"BBL not found: {exc}")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": str(exc)})

    @app.exception_handler(InvalidAddressError)
    async def invalid_address_handler(request: Request, exc: InvalidAddressError) -> JSONResponse:
        """Handles InvalidAddressErrors.

        Args:
            request (Request): The incoming request.
            exc (InvalidAddressError): The InvalidAddressError that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        logger.warning(f"Invalid address: {exc}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})

    @app.exception_handler(AddressNotFoundError)
    async def address_not_found_handler(request: Request, exc: AddressNotFoundError) -> JSONResponse:
        """Handles AddressNotFoundErrors.

        Args:
            request (Request): The incoming request.
            exc (AddressNotFoundError): The AddressNotFoundError that was raised.

        Returns:
            JSONResponse: A JSON response with a 404 status code and the exception's message.
        """
        logger.warning(f"Address not found: {exc}")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": str(exc)})

    @app.exception_handler(MissingApiKeyError)
    async def missing_api_key_handler(request: Request, exc: MissingApiKeyError) -> JSONResponse:
        """Handles MissingApiKeyErrors.

        Args:
            request (Request): The incoming request.
            exc (MissingApiKeyError): The MissingApiKeyError that was raised.

        Returns:
            JSONResponse: A JSON response with a 401 status code and the exception's message.
        """
        logger.warning(f"Missing API key: {exc}")
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": str(exc)})

    @app.exception_handler(InvalidApiKeyError)
    async def invalid_api_key_handler(request: Request, exc: InvalidApiKeyError) -> JSONResponse:
        """Handles InvalidApiKeyErrors.

        Args:
            request (Request): The incoming request.
            exc (InvalidApiKeyError): The InvalidApiKeyError that was raised.

        Returns:
            JSONResponse: A JSON response with a 401 status code and the exception's message.
        """
        logger.warning(f"Invalid API key: {exc}")
        return JSONResponse(status_code=status.HTTP_401_UNAUTHORIZED, content={"message": str(exc)})

    @app.exception_handler(InvalidAdminKeyError)
    async def invalid_admin_key_handler(request: Request, exc: InvalidAdminKeyError) -> JSONResponse:
        """Handles InvalidAdminKeyErrors.

        Args:
            request (Request): The incoming request.
            exc (InvalidAdminKeyError): The InvalidAdminKeyError that was raised.

        Returns:
            JSONResponse: A JSON response with a 403 status code and the exception's message.
        """
        logger.warning(f"Invalid admin key: {exc}")
        return JSONResponse(status_code=status.HTTP_403_FORBIDDEN, content={"message": str(exc)})

    @app.exception_handler(APIKeyNotFoundError)
    async def api_key_not_found_handler(request: Request, exc: APIKeyNotFoundError) -> JSONResponse:
        """Handles APIKeyNotFoundErrors.

        Args:
            request (Request): The incoming request.
            exc (APIKeyNotFoundError): The APIKeyNotFoundError that was raised.

        Returns:
            JSONResponse: A JSON response with a 404 status code and the exception's message.
        """
        logger.warning(f"API key not found: {exc}")
        return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"message": str(exc)})

    @app.exception_handler(InvalidUpdateError)
    async def invalid_update_handler(request: Request, exc: InvalidUpdateError) -> JSONResponse:
        """Handles InvalidUpdateErrors.

        Args:
            request (Request): The incoming request.
            exc (InvalidUpdateError): The InvalidUpdateError that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        logger.warning(f"Invalid update request: {exc}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})

    @app.exception_handler(MissingAdminKeyError)
    async def missing_admin_key_handler(request: Request, exc: MissingAdminKeyError) -> JSONResponse:
        """Handles MissingAdminKeyErrors.

        Args:
            request (Request): The incoming request.
            exc (MissingAdminKeyError): The MissingAdminKeyError that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and the exception's message.
        """
        logger.error(f"Missing admin key: {exc}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)})

    @app.exception_handler(FailedToCreateApiKeyError)
    async def failed_to_create_api_key_handler(request: Request, exc: FailedToCreateApiKeyError) -> JSONResponse:
        """Handles FailedToCreateApiKeyErrors.

        Args:
            request (Request): The incoming request.
            exc (FailedToCreateApiKeyError): The FailedToCreateApiKeyError that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and the exception's message.
        """
        logger.error(f"Failed to create API key: {exc}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)})

    @app.exception_handler(FailedToDeleteApiKeyError)
    async def failed_to_delete_api_key_handler(request: Request, exc: FailedToDeleteApiKeyError) -> JSONResponse:
        """Handles FailedToDeleteApiKeyErrors.

        Args:
            request (Request): The incoming request.
            exc (FailedToDeleteApiKeyError): The FailedToDeleteApiKeyError that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and the exception's message.
        """
        logger.error(f"Failed to delete API key: {exc}")
        return JSONResponse(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": str(exc)})

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError) -> JSONResponse:
        """Handles DatabaseErrors.

        Args:
            request (Request): The incoming request.
            exc (DatabaseError): The DatabaseError that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and a generic error message.
        """
        logger.error(f"Database error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, content={"message": "A database error occurred"}
        )

    @app.exception_handler(GeolocationError)
    async def geolocation_error_handler(request: Request, exc: GeolocationError) -> JSONResponse:
        """Handles GeolocationErrors.

        Args:
            request (Request): The incoming request.
            exc (GeolocationError): The GeolocationError that was raised.

        Returns:
            JSONResponse: A JSON response with a 503 status code and the exception's message.
        """
        logger.error(f"Geolocation error: {exc}")
        return JSONResponse(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, content={"message": str(exc)})

    @app.exception_handler(AddressNotInNewYorkError)
    async def address_not_in_ny_handler(request: Request, exc: AddressNotInNewYorkError) -> JSONResponse:
        """Handles AddressNotInNewYorkErrors.

        Args:
            request (Request): The incoming request.
            exc (AddressNotInNewYorkError): The AddressNotInNewYorkError that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        logger.warning(f"Address not in New York: {exc}")
        return JSONResponse(status_code=status.HTTP_400_BAD_REQUEST, content={"message": str(exc)})
