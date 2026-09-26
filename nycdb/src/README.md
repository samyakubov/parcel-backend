# NYCDB

Python library and CLI for downloading the NYC housing datasets this backend uses and loading them into DuckDB.

## Setup

```sh
python3 -m venv venv
source venv/bin/activate
pip install -e ./src
```

Downloaded files go in `./data`. Use `--root-dir` to change that.

## Commands

List datasets:

```sh
nycdb --list-datasets
```

Download, load, and verify one dataset:

```sh
nycdb --download pluto_latest
nycdb --load pluto_latest
nycdb --verify pluto_latest
```

`--load` writes `nycdb.duckdb` in the working directory. `--drop` deletes that dataset's tables from the file.

Verify every dataset:

```sh
nycdb --verify-all
```

## Datasets

- `acris`
- `pluto_latest`
- `dobjobs` (`dobjobs` and `dob_now_jobs`)
- `dof_sales`
- `dof_annual_sales`
- `ecb_violations`
- `dob_violations`
- `dob_complaints`
