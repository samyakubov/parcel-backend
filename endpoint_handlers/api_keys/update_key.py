from typing import Optional
from database_connector import db

def update_key(key_id: int, name: Optional[str] = None, enabled: Optional[bool] = None) -> bool:
    """
    Update API key properties (name and/or enabled status).
    Returns True if key was updated, False if key didn't exist.
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


def update_last_used(api_key: str):
    """
    Update the last_used_at timestamp for a key.
    Called when a key is successfully used for authentication.
    """
    query = """
            UPDATE api_keys
            SET last_used_at = CURRENT_TIMESTAMP
            WHERE key = ?
            """
    db.execute(query, [api_key])