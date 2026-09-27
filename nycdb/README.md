# nycdb

This is a stripped copy of [nycdb](https://github.com/nycdb/nycdb), kept so this backend can download and load the NYC housing datasets it queries. The loader writes a DuckDB file, `nycdb.duckdb`.

The property API reads tables built from these datasets:

- `acris` — real and personal property master, legals, and parties, plus document-control and property-type codes
- `pluto_latest` — Department of City Planning PLUTO
- `dobjobs` — DOB BIS job filings and DOB NOW job filings (`dob_now_jobs`)
- `dof_sales` — Department of Finance rolling sales
- `dof_annual_sales` — Department of Finance annualized sales
- `ecb_violations` — ECB violations
- `dob_violations` — DOB violations
- `dob_complaints` — DOB complaints

Aggregation SQL in the parent repo's `sql/` directory reshapes those tables for the API.

See [src/README.md](src/README.md) for how to load a dataset.

#### License: AGPLv3

```
NYCDB - database of NYC housing data
Copyright (C) 2016-2020 ziggy & contributors

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
GNU Affero General Public License for more details.
```
