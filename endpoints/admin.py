import os

from fastapi import APIRouter, Header
from starlette import status
from starlette.responses import JSONResponse

from exceptions.api_key_exceptions import InvalidAdminKeyError, MissingAdminKeyError
from logger_config import logger

admin_routes = APIRouter(prefix="/admin")

@admin_routes.post("/authenticate")
def verify_admin_key(password: str = Header(..., alias="X-API-Key")) -> JSONResponse:
    """Verifies the request is using the admin API key.

    Args:
        password (str, optional): The API key from the "X-API-Key" header.
            Defaults to Header(..., alias="X-API-Key").

    Raises:
        MissingAdminKeyError: If the admin key is not configured.
        InvalidAdminKeyError: If the provided API key is invalid.
    """
    admin_key = os.getenv("ADMIN_PASSWORD")

    if not admin_key:
        logger.error("Admin password not configured")
        raise MissingAdminKeyError("Admin password not configured")

    if password != admin_key:
        logger.error("Invalid admin password")
        raise InvalidAdminKeyError("Invalid admin password")

    return JSONResponse(status_code=status.HTTP_200_OK, content={"message": "" })
