from endpoint_handlers.api_keys.exceptions import MissingApiKeyException, InvalidApiKeyException, \
    InvalidAdminKeyException
from endpoint_handlers.property_search.exceptions import InvalidBBLException, BBLNotFoundException, InvalidAddressException, AddressNotFoundException
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse

def register_exception_handlers(app):
    """Registers exception handlers for the FastAPI application.

    Args:
        app (FastAPI): The FastAPI application instance.
    """
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        """Handles HTTPExceptions.

        Args:
            request (Request): The incoming request.
            exc (HTTPException): The HTTPException that was raised.

        Returns:
            JSONResponse: A JSON response with the exception's status code and a generic error message.
        """
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": "An error occurred while processing your request"}
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
        return JSONResponse(
            status_code=400,
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
        return JSONResponse(
            status_code=404,
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
        return JSONResponse(
            status_code=401,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidApiKeyException)
    async def invalid_api_key_handler(request: Request, exc: InvalidApiKeyException):
        """Handles InvalidApiKeyExceptions.

        Args:
            request (Request): The incoming request.
            exc (InvalidApiKeyException): The InvalidApiKeyException that was raised.

        Returns:
            JSONResponse: A JSON response with a 400 status code and the exception's message.
        """
        return JSONResponse(
            status_code=400,
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
        return JSONResponse(
            status_code=403,
            content={"message": str(exc)}
        )

    @app.exception_handler(MissingApiKeyException)
    async def missing_api_key_handler(request: Request, exc: MissingApiKeyException):
        """Handles MissingApiKeyExceptions.

        Args:
            request (Request): The incoming request.
            exc (MissingApiKeyException): The MissingApiKeyException that was raised.

        Returns:
            JSONResponse: A JSON response with a 500 status code and the exception's message.
        """
        return JSONResponse(
            status_code=500,
            content={"message": str(exc)}
        )
