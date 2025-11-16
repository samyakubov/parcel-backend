from database_connector import DatabaseConnector
from endpoint_handlers.api_keys.exceptions import FailedToDeleteApiKeyException
from logger_config import logger

def delete_key(key_id: int, db: DatabaseConnector) -> bool:
    """Deletes an API key by its ID.

    Args:
        key_id (int): The ID of the API key to delete.
        db (DatabaseConnector): The database connector instance.

    Returns:
        bool: True if the key was deleted, False if the key didn't exist.

    Raises:
        FailedToDeleteApiKeyException: If the key could not be deleted.
    """
    if not isinstance(key_id, int):
        logger.error(f"Invalid key ID type for deletion: {type(key_id)}. Must be an integer.")
        return False
        
    try:
        logger.info(f"Attempting to delete API key with ID: {key_id}")
        
        # First, check if the key exists to provide better logging
        check_query = "SELECT COUNT(*) FROM api_keys WHERE id = ?"
        result = db.execute(check_query, [key_id])
        if result[0][0] == 0:
            logger.warning(f"Attempted to delete an API key that does not exist with ID: {key_id}")
            return False

        # If it exists, proceed with deletion
        query = "DELETE FROM api_keys WHERE id = ?"
        db.execute(query, [key_id])

        # Verify deletion
        result = db.execute(check_query, [key_id])
        if result[0][0] == 0:
            logger.info(f"Successfully deleted API key with ID: {key_id}")
            return True
        else:
            # This case should be rare but indicates a problem
            logger.error(f"Failed to delete API key with ID: {key_id} even though it existed.")
            raise FailedToDeleteApiKeyException

    except Exception as e:
        logger.error(f"An unexpected error occurred while deleting API key with ID {key_id}: {e}", exc_info=True)
        raise FailedToDeleteApiKeyException from e