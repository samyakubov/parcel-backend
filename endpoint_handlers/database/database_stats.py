from fastapi import HTTPException

from database_connector import DatabaseConnector


def database_stats(db: DatabaseConnector):
    """Get database statistics"""
    try:

        tables = db.execute("SHOW TABLES")
        stats = []

        for table in tables:
            table_name = table[0]
            count = db.execute(f"SELECT COUNT(*) FROM {table_name}")[0][0]
            stats.append({
                "table": table_name,
                "row_count": count
            })

        return {
            "tables": stats
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))