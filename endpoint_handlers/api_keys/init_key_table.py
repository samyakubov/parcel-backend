from database_connector import db

def init_key_table():
    """Initializes the `api_keys` table in the database.

    This function creates the `api_keys` table if it does not already exist.
    It also creates a sequence for the auto-incrementing primary key.
    """
    # Create sequence for auto-incrementing ID
    sequence_query = """
        CREATE SEQUENCE IF NOT EXISTS api_keys_id_seq START 1;
        """
    db.execute(sequence_query)

    create_table_query = """
                         CREATE TABLE IF NOT EXISTS api_keys (
                             id INTEGER PRIMARY KEY DEFAULT nextval('api_keys_id_seq'),
                             key VARCHAR UNIQUE NOT NULL,
                             name VARCHAR NOT NULL,
                             enabled BOOLEAN NOT NULL DEFAULT true,
                             created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                             updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                             last_used_at TIMESTAMP
                             ); \
                         """
    db.execute(create_table_query)