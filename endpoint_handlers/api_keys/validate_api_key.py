from fastapi import Depends, Header

from database_connector import DatabaseConnector, get_db
from endpoint_handlers.api_keys.update_key import update_last_used
from exceptions.api_key_exceptions import InvalidApiKeyError, MissingApiKeyError
from logger_config import logger


async def validate_api_key(
    x_api_key: str | None = Header(None, alias="X-API-Key"), db: DatabaseConnector = Depends(get_db)
) -> None:
    """FastAPI dependency that validates an API key from the X-API-Key header.

    Args:
        x_api_key (Optional[str], optional): The API key from the X-API-Key header.
            Defaults to Header(None, alias="X-API-Key").
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Raises:
        MissingApiKeyError: If the API key is missing.
        InvalidApiKeyError: If the API key is invalid or disabled.
    """

    if not x_api_key:
        logger.error("Authentication failed: Missing API key")
        raise MissingApiKeyError("API key is required")

    query = """
            SELECT id, key, name, enabled, created_at, updated_at, last_used_at
            FROM api_keys
            WHERE key = ? AND enabled = true
            """
    is_valid_key = db.execute(query, [x_api_key])

    partial_key = x_api_key[:8] if len(x_api_key) >= 8 else x_api_key

    if not is_valid_key:
        logger.error(f"Authentication failed: Invalid API key ({partial_key}...)")
        raise InvalidApiKeyError("Invalid or disabled API key")

    update_last_used(x_api_key, db=db)

    logger.info("Authentication successful with given api key \n")
