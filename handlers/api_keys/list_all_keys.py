from database_connector import DatabaseConnector
from schemas import APIKeyConfig


def list_all_keys(db: DatabaseConnector) -> list[APIKeyConfig]:
    """Lists all API keys from the database.

    Note:
        This function returns the full key values. The caller is responsible for
        filtering sensitive data before displaying it.

    Args:
        db (DatabaseConnector): The database connector instance.

    Returns:
        List[APIKeyConfig]: A list of all API keys.
    """
    query = """
            SELECT id, key, name, enabled, created_at, updated_at, last_used_at
            FROM api_keys
            ORDER BY created_at DESC \
            """
    result = db.execute(query)

    keys = []
    for row in result:
        keys.append(
            APIKeyConfig(
                id=row[0],
                key=row[1],
                name=row[2],
                enabled=row[3],
                created_at=row[4],
                updated_at=row[5],
                last_used_at=row[6],
            )
        )

    return keys
