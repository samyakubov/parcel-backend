def create_table(table_name, fields) -> str:
    """
    String, Iterable --> String
    """
    sql = f"CREATE TABLE {table_name} ("
    sql += ", ".join([f"{field} {fields[field]}" for field in fields])
    sql += ")"
    return sql


def drop_table(table_name) -> str:
    """
    String --> String
    """
    return f"DROP TABLE IF EXISTS {table_name}"
