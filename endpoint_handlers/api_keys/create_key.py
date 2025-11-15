import secrets
from endpoint_handlers.api_keys.api_key_config import APIKeyConfig
from database_connector import db
from endpoint_handlers.api_keys.exceptions import FailedToCreateApiKeyException
from logger_config import logger

def create_key(name: str) -> APIKeyConfig:
    """
    Generate and store a new API key.
    Returns the created APIKeyConfig with the generated key.
    """
    if not name:
        logger.warning("Attempted to create an API key without a name.")
        raise ValueError("API key name cannot be empty.")
        
    try:
        logger.info(f"Attempting to create a new API key with name: '{name}'")
        # Generate cryptographically secure random key
        api_key = secrets.token_urlsafe(32)

        query = """
                INSERT INTO api_keys (key, name, enabled, created_at, updated_at)
                VALUES (?, ?, true, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                    RETURNING id, key, name, enabled, created_at, updated_at, last_used_at
                """
        result = db.execute(query, [api_key, name])
        if not result:
            logger.error(f"Database insertion failed when creating API key for name: '{name}'")
            raise FailedToCreateApiKeyException

        row = result[0]
        key_config = APIKeyConfig(
            id=row[0],
            key=row[1],
            name=row[2],
            enabled=row[3],
            created_at=row[4],
            updated_at=row[5],
            last_used_at=row[6]
        )
        logger.info(f"Successfully created API key with ID {key_config.id} and name '{key_config.name}'.")
        return key_config
    except Exception as e:
        logger.error(f"An unexpected error occurred while creating an API key for name '{name}': {e}", exc_info=True)
        raise FailedToCreateApiKeyException from e