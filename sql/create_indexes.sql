-- Performance indexes for nycdb.duckdb
-- Run once with write access: duckdb nycdb.duckdb < sql/create_indexes.sql
--
-- These indexes target the columns used in WHERE clauses across all query handlers.
-- Expected improvement: 10-15 second queries -> sub-second queries

-- Primary lookup indexes for aggregated_acris_records (largest table, ~11GB)
-- Used by: search_by_property_address, get_current_home_owner, get_previous_owners,
--          get_building_shareholders, get_last_sold, get_mortgage
CREATE INDEX IF NOT EXISTS idx_acris_search_address ON aggregated_acris_records(search_prop_address);
CREATE INDEX IF NOT EXISTS idx_acris_bbl ON aggregated_acris_records(bbl);
CREATE INDEX IF NOT EXISTS idx_acris_bbl_doctype ON aggregated_acris_records(bbl, doc_type);
CREATE INDEX IF NOT EXISTS idx_acris_documentid ON aggregated_acris_records(documentid);
CREATE INDEX IF NOT EXISTS idx_acris_street ON aggregated_acris_records(prop_streetnumber, prop_streetname);

-- dobjobs table - used by get_job_filings, get_phone_number_by_bbl
CREATE INDEX IF NOT EXISTS idx_dobjobs_bbl ON dobjobs(bbl);

-- dob_complaints table - used by get_complaints
CREATE INDEX IF NOT EXISTS idx_complaints_address ON dob_complaints(housenumber, housestreet);

-- zoning table - used by get_zoning
CREATE INDEX IF NOT EXISTS idx_zoning_bbl ON zoning(bbl);

-- aggregated_dof_sales table - used by get_last_sold
CREATE INDEX IF NOT EXISTS idx_dof_sales_bbl ON aggregated_dof_sales(bbl);

-- aggregated_acris_violations table - used by get_violations
CREATE INDEX IF NOT EXISTS idx_violations_bbl ON aggregated_acris_violations(bbl);

-- pluto_latest table - used in JOINs with aggregated_acris_records
CREATE INDEX IF NOT EXISTS idx_pluto_bbl ON pluto_latest(bbl);
