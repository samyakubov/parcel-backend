from endpoint_handlers.api_keys.exceptions import MissingApiKeyException, InvalidApiKeyException, \
    InvalidAdminKeyException
from endpoint_handlers.property_search.exceptions import InvalidBBLException, BBLNotFoundException, InvalidAddressException, AddressNotFoundException
from fastapi import Request, status, HTTPException
from fastapi.responses import JSONResponse

def register_exception_handlers(app):
    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        return JSONResponse(
            status_code=exc.status_code,
            content={"message": "An error occurred while processing your request"}
        )
    @app.exception_handler(InvalidBBLException)
    async def invalid_bbl_handler(request: Request, exc: InvalidBBLException):
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={"message": str(exc)}
        )

    @app.exception_handler(BBLNotFoundException)
    async def bbl_not_found_handler(request: Request, exc: BBLNotFoundException):
        return JSONResponse(
            status_code=status.HTTP_404_NOT_FOUND,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidAddressException)
    async def invalid_address_handler(request: Request, exc: InvalidAddressException):
        return JSONResponse(
            status_code=400,
            content={"message": str(exc)}
        )

    @app.exception_handler(AddressNotFoundException)
    async def address_not_found_handler(request: Request, exc: AddressNotFoundException):
        return JSONResponse(
            status_code=404,
            content={"message": str(exc)}
        )

    @app.exception_handler(MissingApiKeyException)
    async def missing_api_key_handler(request: Request, exc: MissingApiKeyException):
        return JSONResponse(
            status_code=401,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidApiKeyException)
    async def invalid_api_key_handler(request: Request, exc: InvalidApiKeyException):
        return JSONResponse(
            status_code=400,
            content={"message": str(exc)}
        )

    @app.exception_handler(InvalidAdminKeyException)
    async def invalid_admin_key_handler(request: Request, exc: InvalidAdminKeyException):
        return JSONResponse(
            status_code=403,
            content={"message": str(exc)}
        )

    @app.exception_handler(MissingApiKeyException)
    async def missing_api_key_handler(request: Request, exc: MissingApiKeyException):
        return JSONResponse(
            status_code=500,
            content={"message": str(exc)}
        )
