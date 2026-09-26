from types import SimpleNamespace
from unittest.mock import patch

import nycdb

ARGS = SimpleNamespace(
    root_dir="./data",
    hide_progress=True,
)


def test_datasets():
    names = set(nycdb.datasets().keys())
    assert names == {
        "acris",
        "dob_complaints",
        "dob_violations",
        "dobjobs",
        "dof_annual_sales",
        "dof_sales",
        "ecb_violations",
        "pluto_latest",
    }


def test_dataset():
    d = nycdb.Dataset("pluto_latest", args=ARGS)

    assert d.name == "pluto_latest"
    assert d.dataset == nycdb.datasets()["pluto_latest"]
    assert isinstance(d.files, list)
    assert len(d.files) == 1
    assert isinstance(d.files[0], nycdb.File)


@patch("nycdb.database.duckdb.connect")
def test_setup_db(mock_connect):
    d = nycdb.Dataset("pluto_latest", args=ARGS)
    assert d.db is None
    d.setup_db()
    d.setup_db()
    assert isinstance(d.db, nycdb.Database)
    assert mock_connect.call_count == 1
