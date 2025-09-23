import duckdb

class DatabaseConnector:
    def __init__(self, db_path=":memory:"):
        self.db_path = db_path
        self.conn = None

    def connect(self):
        if not self.conn:
            self.conn = duckdb.connect(self.db_path)
        return self.conn

    def execute(self, query, params=None):
        conn = self.connect()
        if params:
            return conn.execute(query, params).fetchall()
        return conn.execute(query).fetchall()

    def execute_df(self, query, params=None):
        conn = self.connect()
        if params:
            return conn.execute(query, params).df()
        return conn.execute(query).df()

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None


db = DatabaseConnector("nycdb.duckdb")