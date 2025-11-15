from fastapi import Header
from typing import Optional
from database_connector import db
from endpoint_handlers.api_keys.api_key_config import APIKeyConfig
from endpoint_handlers.api_keys.exceptions import MissingApiKeyException, InvalidApiKeyException
from endpoint_handlers.api_keys.update_key import update_last_used
from logger_config import logger

async def validate_api_key(x_api_key: Optional[str] = Header(None, alias="X-API-Key")):
    """FastAPI dependency that validates an API key from the X-API-Key header.

    Args:
        x_api_key (Optional[str], optional): The API key from the X-API-Key header. 
            Defaults to Header(None, alias="X-API-Key").

    Raises:
        MissingApiKeyException: If the API key is missing.
        InvalidApiKeyException: If the API key is invalid or disabled.
    """

    # Check if API key is provided
    if not x_api_key:
        logger.error("Authentication failed: Missing API key")
        raise MissingApiKeyException


    query = """
            SELECT id, key, name, enabled, created_at, updated_at, last_used_at
            FROM api_keys
            WHERE key = ? AND enabled = true
            """
    is_valid_key = db.execute(query, [x_api_key])

    partial_key = x_api_key[:8] if len(x_api_key) >= 8 else x_api_key

    if not is_valid_key:
        # Log authentication failure with partial key (first 8 chars)
        logger.error(f"Authentication failed: Invalid API key ({partial_key}...)")
        raise InvalidApiKeyException

    # Update last_used_at timestamp
    update_last_used(x_api_key)

    logger.info(f"Authentication successful with given Key")