from database_connector import DatabaseConnector


def update_key(key_id: int, db: DatabaseConnector, name: str | None = None, enabled: bool | None = None) -> bool:
    """Updates the properties of an API key.

    NOTE: Disabled - database is in read_only mode. Use DuckDB CLI to update keys manually.

    Args:
        key_id (int): The ID of the API key to update.
        db (DatabaseConnector): The database connector instance.
        name (Optional[str], optional): The new name for the API key. Defaults to None.
        enabled (Optional[bool], optional): The new enabled status for the API key. Defaults to None.

    Raises:
        NotImplementedError: Always raised - writes are disabled.
    """
    raise NotImplementedError(
        "API key update is disabled. Database is in read_only mode. "
        "Use DuckDB CLI to update keys manually."
    )
    # Original implementation commented out - database is read_only
    # updates = []
    # params = []
    #
    # if name is not None:
    #     updates.append("name = ?")
    #     params.append(name)
    #
    # if enabled is not None:
    #     updates.append("enabled = ?")
    #     params.append(enabled)
    #
    # if not updates:
    #     return False
    #
    # updates.append("updated_at = CURRENT_TIMESTAMP")
    #
    # query = f"UPDATE api_keys SET {', '.join(updates)} WHERE id = ?"
    # params.append(key_id)
    #
    # db.execute(query, params)
    #
    # check_query = "SELECT COUNT(*) FROM api_keys WHERE id = ?"
    # result = db.execute(check_query, [key_id])
    #
    # return result[0][0] > 0


def update_last_used(api_key: str, db: DatabaseConnector) -> None:
    """Updates the last_used_at timestamp for an API key.

    NOTE: Disabled - database is in read_only mode. This is a no-op.

    Args:
        api_key (str): The API key that was used.
        db (DatabaseConnector): The database connector instance.
    """
    # Disabled - database is read_only, last_used_at tracking not available
    pass
    # Original implementation:
    # query = """
    #         UPDATE api_keys
    #         SET last_used_at = CURRENT_TIMESTAMP
    #         WHERE key = ?
    #         """
    # db.execute(query, [api_key])
