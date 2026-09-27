from collections import OrderedDict

import nycdb


def test_create_table():
    fields = OrderedDict([("address", "text"), ("block", "integer")])
    assert nycdb.sql.create_table("hello", fields) == "CREATE TABLE hello (address text, block integer)"


def test_create_table_serial_uses_a_duckdb_sequence():
    fields = OrderedDict([("name", "text"), ("id", "serial PRIMARY KEY")])
    statement = nycdb.sql.create_table("sales", fields)
    assert "CREATE SEQUENCE sales_id_seq" in statement
    assert "id INTEGER PRIMARY KEY DEFAULT nextval('sales_id_seq')" in statement
    assert "serial" not in statement.lower()
