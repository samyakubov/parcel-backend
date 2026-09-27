import csv
import os
import tempfile

import duckdb


def _quote_ident(name):
    return '"' + str(name).replace('"', '""') + '"'


class Database:
    """
    Database connection. This is a wrapper around duckdb.connect, accessible at .conn
    """

    def __init__(self, args, table_name=None):
        """
        args is a Namespace that must contain: db_path
        """
        self.db_path = "nycdb.duckdb"
        self.table_name = table_name
        self.conn = duckdb.connect(self.db_path)
        self.conn.execute("INSTALL spatial;")
        self.conn.execute("LOAD spatial;")

    def sql(self, statement):
        """executes single sql statement"""
        self.conn.execute(statement)

    def insert_rows(self, rows, table_name=None):
        """
        Insert rows by column name.

        A positional COPY shifts values whenever the row order differs from
        the table (computed columns such as bbl are appended, and source
        headers are lowercase). Naming the columns keeps dates and amounts
        in the fields they belong to.
        """
        if table_name is None:
            table_name = self.table_name

        if not rows:
            return

        columns = list(rows[0].keys())
        quoted_columns = ", ".join(_quote_ident(column) for column in columns)

        with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".csv", newline="") as temp:
            file_path = temp.name
            writer = csv.writer(temp)
            writer.writerow(columns)
            for row in rows:
                writer.writerow(row.values())

        try:
            self.conn.execute(
                f"INSERT INTO {_quote_ident(table_name)} ({quoted_columns}) "
                "SELECT * FROM read_csv(?, header=true, all_varchar=true, nullstr='')",
                [file_path],
            )
        finally:
            os.remove(file_path)

    def execute_sql_file(self, sql_file):
        """
        Executes the provided sql file.
        It assumes the path is relative to ./sql
        """
        file_path = os.path.join(os.path.dirname(__file__), "sql", sql_file)

        with open(file_path, encoding="utf-8") as f:
            self.sql(f.read())

    def execute_and_fetchone(self, query):
        """
        Execute the given query and returns the first row
        """
        return self.conn.execute(query).fetchone()[0]

    def table_exists(self, table_name):
        """Tests if the table exists"""
        query = f"SELECT 1 FROM information_schema.tables WHERE table_name = '{table_name}'"
        return self.conn.execute(query).fetchone() is not None

    def row_count(self, table_name):
        """returns the row count of the table"""
        query = f"SELECT COUNT(*) from {table_name}"
        return self.execute_and_fetchone(query)
