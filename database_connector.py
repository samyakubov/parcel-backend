import os
import duckdb
import pandas as pd
from logger_config import logger


class DatabaseError(Exception):
    """Exception raised for database-related errors."""

    pass


class DatabaseConnector:
    _instance = None

    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.conn = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            db_path = os.getenv("DATABASE_PATH", ":memory:")
            cls._instance = cls(db_path)
            cls._instance.connect()
        return cls._instance

    def connect(self) -> duckdb.DuckDBPyConnection:
        if not self.conn:
            try:
                self.conn = duckdb.connect(self.db_path, read_only=True, config={
                    'memory_limit': '2GB',
                    'threads': 2
                })
            except Exception as e:
                logger.error(f"Failed to connect to database at '{self.db_path}': {e}", exc_info=True)
                raise DatabaseError(f"Database connection failed: {e}") from e
        return self.conn

    def execute(self, query, params=None) -> list:
        """Executes a SQL query and fetches all results.

        Args:
            query (str): The SQL query to execute.
            params (list, optional): A list of parameters to substitute into the query.
                Defaults to None.

        Returns:
            list: A list of tuples representing the query results.

        Raises:
            DatabaseError: If the query execution fails.
        """
        try:
            conn = self.connect()
            if params:
                return conn.execute(query, params).fetchall()
            return conn.execute(query).fetchall()
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            logger.error(f"Database query execution failed: {e}", exc_info=True)
            raise DatabaseError(f"Query execution failed: {e}") from e

    def execute_df(self, query, params=None) -> pd.DataFrame:
        """Executes a SQL query and returns the results as a Pandas DataFrame.

        Args:
            query (str): The SQL query to execute.
            params (list, optional): A list of parameters to substitute into the query.
                Defaults to None.

        Returns:
            pandas.DataFrame: A DataFrame containing the query results.

        Raises:
            DatabaseError: If the query execution fails.
        """
        try:
            conn = self.connect()
            if params:
                return conn.execute(query, params).df()
            return conn.execute(query).df()
        except Exception as e:
            if isinstance(e, DatabaseError):
                raise
            logger.error(f"Database query execution failed: {e}", exc_info=True)
            raise DatabaseError(f"Query execution failed: {e}") from e

    def close(self) -> None:
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


def get_db():
    yield DatabaseConnector.get_instance()
