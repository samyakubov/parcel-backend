from types import SimpleNamespace
from unittest.mock import patch

import nycdb

ARGS = SimpleNamespace(root_dir="/tmp/nycdb_test_data")


@patch("nycdb.database.duckdb.connect")
def test_init(mock_connect):
    db = nycdb.Database(ARGS, "test_table")
    assert mock_connect.call_count == 1
    mock_connect.return_value.execute.assert_any_call("INSTALL spatial;")
    mock_connect.return_value.execute.assert_any_call("LOAD spatial;")

    assert db.table_name == "test_table"
    assert db.db_path == "nycdb.duckdb"
