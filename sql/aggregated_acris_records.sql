CREATE TABLE aggregated_acris_records AS
WITH property_records AS (
    SELECT
        per.documentid,
        per.rpl_bbl AS bbl,
        per.rpm_docamount AS amount,
        per.rpl_borough AS prop_borough,
        per.rpl_block AS prop_block,
        per.rpl_lot AS prop_lot,
        per.rpl_unit AS prop_unit,
        per.rpl_streetnumber AS prop_streetnumber,
        per.rpl_streetname AS prop_streetname,
        per.rpl_partiallot,
        per.dcc_partytype_desc AS partytype_desc,
        per.rpp_name AS party_name,
        per.rpp_address1 AS party_address1,
        per.rpp_address2 AS party_address2,
        per.rpp_country AS party_country,
        per.rpp_city AS party_city,
        per.rpp_state AS party_state,
        per.rpp_zip AS party_zip,
        per.apc_property_description AS prop_type,
        per.dcc_doctypedescription AS doc_type,
        per.rpm_recordedfiled AS recordedfiled,
        per.rpm_goodthroughdate AS m_goodthroughdate
    FROM nycdb.main.vw_real_property_records per

    UNION ALL

    SELECT
        per.documentid,
        per.rpl_bbl AS bbl,
        per.rpm_docamount AS amount,
        per.rpl_borough AS prop_borough,
        per.rpl_block AS prop_block,
        per.rpl_lot AS prop_lot,
        per.rpl_unit AS prop_unit,
        per.rpl_streetnumber AS prop_streetnumber,
        per.rpl_streetname AS prop_streetname,
        per.rpl_partiallot,
        per.dcc_partytype_desc AS partytype_desc,
        per.rpp_name AS party_name,
        per.rpp_address1 AS party_address1,
        per.rpp_address2 AS party_address2,
        per.rpp_country AS party_country,
        per.rpp_city AS party_city,
        per.rpp_state AS party_state,
        per.rpp_zip AS party_zip,
        per.apc_property_description AS prop_type,
        per.dcc_doctypedescription AS doc_type,
        per.rpm_recordedfiled AS recordedfiled,
        per.rpm_goodthroughdate AS m_goodthroughdate
    FROM nycdb.main.vw_personal_property_records per
)
SELECT
    pr.*,
    CASE
        WHEN pr.rpl_partiallot = 'P' THEN 'Partial'
        WHEN pr.rpl_partiallot = 'E' THEN 'Entire'
        ELSE ''
        END AS prop_partiallot,
    UPPER(normalize_property_address(pr.prop_streetnumber, pr.prop_streetname, pr.prop_borough)) AS search_prop_address
FROM property_records pr;

DROP VIEW nycdb.main.vw_personal_property_records;
DROP VIEW nycdb.main.vw_real_property_records;
