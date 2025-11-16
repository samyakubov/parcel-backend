import logging
from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from starlette import status
from exceptions.api_key_exceptions import MissingApiKeyException, InvalidApiKeyException, InvalidAdminKeyException, \
    APIKeyNotFoundException, InvalidUpdateException, MissingAdminKeyException, FailedToCreateApiKeyException, \
    FailedToDeleteApiKeyException
from exceptions.property_search_exceptions import InvalidBBLException, BBLNotFoundException, InvalidAddressException, \
    AddressNotFoundException
from exceptions.geolocation_exceptions import GeolocationException, AddressNotInNewYorkException
from database_connector import DatabaseError

logger = logging.getLogger(__name__)


def register_exception_handlers(app):
    """Registers exception handlers for the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handles any unhandled exceptions.

        Args:
            request (Request): The incoming request.
            exc (Exception): The exception that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and a generic error message.
        """
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "An unexpected error occurred."}
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handles HTTPExceptions.

        Args:
            request (Request): The incoming request.
            exc (HTTPException): The HTTPException that was raised.

        Returns:
            JSONResponse: A JSON response with the exception's status code and a generic error message.
        """
        logger.warning(f"HTTPException: {exc.detail}")
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": exc.detail}
        )

    @app.exception_handler(InvalidBBLException)
    async def invalid_bbl_handler(request: Request, exc: InvalidBBLException):
        """Handles InvalidBBLExceptions.

        Args:
            request (Request): The incoming request.
            exc (InvalidBBLException): The InvalidBBLException that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        logger.warning(f"Invalid BBL: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)}
        )

    @app.exception_handler(BBLNotFoundException)
    async def bbl_not_found_handler(request: Request, exc: BBLNotFoundException):
        """Handles BBLNotFoundExceptions.

        Args:
            request (Request): The incoming request.
            exc (BBLNotFoundException): The BBLNotFoundException that was raised.

        Returns:
            JSONResponse: A JSON response with a 404 status code and the exception's message.
        """
        logger.warning(f"BBL not found: {exc}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidAddressException)
    async def invalid_address_handler(request: Request, exc: InvalidAddressException):
        """Handles InvalidAddressExceptions.

        Args:
            request (Request): The incoming request.
            exc (InvalidAddressException): The InvalidAddressException that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        logger.warning(f"Invalid address: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)}
        )

    @app.exception_handler(AddressNotFoundException)
    async def address_not_found_handler(request: Request, exc: AddressNotFoundException):
        """Handles AddressNotFoundExceptions.

        Args:
            request (Request): The incoming request.
            exc (AddressNotFoundException): The AddressNotFoundException that was raised.

        Returns:
            JSONResponse: A JSON response with a 404 status code and the exception's message.
        """
        logger.warning(f"Address not found: {exc}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(exc)}
        )

    @app.exception_handler(MissingApiKeyException)
    async def missing_api_key_handler(request: Request, exc: MissingApiKeyException):
        """Handles MissingApiKeyExceptions.

        Args:
            request (Request): The incoming request.
            exc (MissingApiKeyException): The MissingApiKeyException that was raised.

        Returns:
            JSONResponse: A JSON response with a 401 status code and the exception's message.
        """
        logger.warning(f"Missing API key: {exc}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidApiKeyException)
    async def invalid_api_key_handler(request: Request, exc: InvalidApiKeyException):
        """Handles InvalidApiKeyExceptions.

        Args:
            request (Request): The incoming request.
            exc (InvalidApiKeyException): The InvalidApiKeyException that was raised.

        Returns:
            JSONResponse: A JSON response with a 401 status code and the exception's message.
        """
        logger.warning(f"Invalid API key: {exc}")
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidAdminKeyException)
    async def invalid_admin_key_handler(request: Request, exc: InvalidAdminKeyException):
        """Handles InvalidAdminKeyExceptions.

        Args:
            request (Request): The incoming request.
            exc (InvalidAdminKeyException): The InvalidAdminKeyException that was raised.

        Returns:
            JSONResponse: A JSON response with a 403 status code and the exception's message.
        """
        logger.warning(f"Invalid admin key: {exc}")
        return JSONResponse(
            status_code=status.HTTP_403_FORBIDDEN,
            content={"message": str(exc)}
        )

    @app.exception_handler(APIKeyNotFoundException)
    async def api_key_not_found_handler(request: Request, exc: APIKeyNotFoundException):
        """Handles APIKeyNotFoundExceptions.

        Args:
            request (Request): The incoming request.
            exc (APIKeyNotFoundException): The APIKeyNotFoundException that was raised.

        Returns:
            JSONResponse: A JSON response with a 404 status code and the exception's message.
        """
        logger.warning(f"API key not found: {exc}")
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidUpdateException)
    async def invalid_update_handler(request: Request, exc: InvalidUpdateException):
        """Handles InvalidUpdateExceptions.

        Args:
            request (Request): The incoming request.
            exc (InvalidUpdateException): The InvalidUpdateException that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        logger.warning(f"Invalid update request: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)}
        )

    @app.exception_handler(MissingAdminKeyException)
    async def missing_admin_key_handler(request: Request, exc: MissingAdminKeyException):
        """Handles MissingAdminKeyExceptions.

        Args:
            request (Request): The incoming request.
            exc (MissingAdminKeyException): The MissingAdminKeyException that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and the exception's message.
        """
        logger.error(f"Missing admin key: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(exc)}
        )

    @app.exception_handler(FailedToCreateApiKeyException)
    async def failed_to_create_api_key_handler(request: Request, exc: FailedToCreateApiKeyException):
        """Handles FailedToCreateApiKeyExceptions.

        Args:
            request (Request): The incoming request.
            exc (FailedToCreateApiKeyException): The FailedToCreateApiKeyException that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and the exception's message.
        """
        logger.error(f"Failed to create API key: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(exc)}
        )

    @app.exception_handler(FailedToDeleteApiKeyException)
    async def failed_to_delete_api_key_handler(request: Request, exc: FailedToDeleteApiKeyException):
        """Handles FailedToDeleteApiKeyExceptions.

        Args:
            request (Request): The incoming request.
            exc (FailedToDeleteApiKeyException): The FailedToDeleteApiKeyException that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and the exception's message.
        """
        logger.error(f"Failed to delete API key: {exc}")
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": str(exc)}
        )

    @app.exception_handler(DatabaseError)
    async def database_error_handler(request: Request, exc: DatabaseError):
        """Handles DatabaseErrors.

        Args:
            request (Request): The incoming request.
            exc (DatabaseError): The DatabaseError that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and a generic error message.
        """
        logger.error(f"Database error: {exc}", exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={"message": "A database error occurred"}
        )

    @app.exception_handler(GeolocationException)
    async def geolocation_error_handler(request: Request, exc: GeolocationException):
        """Handles GeolocationExceptions.

        Args:
            request (Request): The incoming request.
            exc (GeolocationException): The GeolocationException that was raised.

        Returns:
            JSONResponse: A JSON response with a 503 status code and the exception's message.
        """
        logger.error(f"Geolocation error: {exc}")
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"message": str(exc)}
        )

    @app.exception_handler(AddressNotInNewYorkException)
    async def address_not_in_ny_handler(request: Request, exc: AddressNotInNewYorkException):
        """Handles AddressNotInNewYorkExceptions.

        Args:
            request (Request): The incoming request.
            exc (AddressNotInNewYorkException): The AddressNotInNewYorkException that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        logger.warning(f"Address not in New York: {exc}")
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)}
        )
