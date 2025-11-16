from typing import Optional
from database_connector import DatabaseConnector

def update_key(key_id: int, db: DatabaseConnector, name: Optional[str] = None, enabled: Optional[bool] = None) -> bool:
    """Updates the properties of an API key.

    Args:
        key_id (int): The ID of the API key to update.
        db (DatabaseConnector): The database connector instance.
        name (Optional[str], optional): The new name for the API key. Defaults to None.
        enabled (Optional[bool], optional): The new enabled status for the API key. Defaults to None.

    Returns:
        bool: True if the key was updated, False if the key didn't exist.
    """
    # Build dynamic update query based on provided parameters
    updates = []
    params = []

    if name is not None:
        updates.append("name = ?")
        params.append(name)

    if enabled is not None:
        updates.append("enabled = ?")
        params.append(enabled)

    if not updates:
        # No updates requested
        return False

    # Always update the updated_at timestamp
    updates.append("updated_at = CURRENT_TIMESTAMP")

    query = f"UPDATE api_keys SET {', '.join(updates)} WHERE id = ?"
    params.append(key_id)

    db.execute(query, params)

    # Check if the key exists
    check_query = "SELECT COUNT(*) FROM api_keys WHERE id = ?"
    result = db.execute(check_query, [key_id])

    return result[0][0] > 0


def update_last_used(api_key: str, db: DatabaseConnector) -> None:
    """Updates the last_used_at timestamp for an API key.

    This function is called when a key is successfully used for authentication.

    Args:
        api_key (str): The API key that was used.
        db (DatabaseConnector): The database connector instance.
    """
    query = """
            UPDATE api_keys
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE key = ?
            """
    db.execute(query, [api_key])