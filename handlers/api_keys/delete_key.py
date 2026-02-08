from database_connector import DatabaseConnector
from exceptions.api_key_exceptions import FailedToDeleteApiKeyError
from logger_config import logger


def delete_key(key_id: int, db: DatabaseConnector) -> bool:
    """Deletes an API key by its ID.

    NOTE: Disabled - database is in read_only mode. Use DuckDB CLI to delete keys manually.

    Args:
        key_id (int): The ID of the API key to delete.
        db (DatabaseConnector): The database connector instance.

    Raises:
        NotImplementedError: Always raised - writes are disabled.
    """
    raise NotImplementedError(
        "API key deletion is disabled. Database is in read_only mode. "
        "Use DuckDB CLI to delete keys manually."
    )
    # Original implementation commented out - database is read_only
    # if not isinstance(key_id, int):
    #     logger.error(f"Invalid key ID type for deletion: {type(key_id)}. Must be an integer.")
    #     return False
    # try:
    #     logger.info(f"Attempting to delete API key with ID: {key_id}")
    #
    #     check_query = "SELECT COUNT(*) FROM api_keys WHERE id = ?"
    #     result = db.execute(check_query, [key_id])
    #     if result[0][0] == 0:
    #         logger.warning(f"Attempted to delete an API key that does not exist with ID: {key_id}")
    #         return False
    #
    #     query = "DELETE FROM api_keys WHERE id = ?"
    #     db.execute(query, [key_id])
    #
    #     result = db.execute(check_query, [key_id])
    #     if result[0][0] == 0:
    #         logger.info(f"Successfully deleted API key with ID: {key_id}")
    #         return True
    #     else:
    #         logger.error(f"Failed to delete API key with ID: {key_id} even though it existed.")
    #         raise FailedToDeleteApiKeyError(f"Failed to delete API key with ID {key_id}")
    #
    # except FailedToDeleteApiKeyError:
    #     raise
    # except Exception as e:
    #     logger.error(f"An unexpected error occurred while deleting API key with ID {key_id}: {e}", exc_info=True)
    #     raise FailedToDeleteApiKeyError(f"Unexpected error deleting API key: {str(e)}") from e
