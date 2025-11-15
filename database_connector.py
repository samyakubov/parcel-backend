import duckdb

class DatabaseConnector:
    """A class to connect to a DuckDB database and execute queries."""

    def __init__(self, db_path=":memory:"):
        """Initializes the DatabaseConnector.

        Args:
            db_path (str, optional): The path to the DuckDB database file. 
                Defaults to ":memory:", which creates an in-memory database.
        """
        self.db_path = db_path
        self.conn = None

    def connect(self):
        """Connects to the DuckDB database.

        Returns:
            duckdb.DuckDBPyConnection: A connection object to the database.
        """
        if not self.conn:
            self.conn = duckdb.connect(self.db_path)
        return self.conn

    def execute(self, query, params=None):
        """Executes a SQL query and fetches all results.

        Args:
            query (str): The SQL query to execute.
            params (list, optional): A list of parameters to substitute into the query. 
                Defaults to None.

        Returns:
            list: A list of tuples representing the query results.
        """
        conn = self.connect()
        if params:
            return conn.execute(query, params).fetchall()
        return conn.execute(query).fetchall()

    def execute_df(self, query, params=None):
        """Executes a SQL query and returns the results as a Pandas DataFrame.

        Args:
            query (str): The SQL query to execute.
            params (list, optional): A list of parameters to substitute into the query.
                Defaults to None.

        Returns:
            pandas.DataFrame: A DataFrame containing the query results.
        """
        conn = self.connect()
        if params:
            return conn.execute(query, params).df()
        return conn.execute(query).df()

    def close(self):
        """Closes the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None


db = DatabaseConnector("nycdb.duckdb")