drop view if exists vw_real_property_records;

CREATE OR REPLACE VIEW vw_real_property_records
AS SELECT
       rpm.documentid AS documentid,
       rpm.docamount AS rpm_docamount,
       rpm.recordedfiled AS rpm_recordedfiled,
       rpm.goodthroughdate AS rpm_goodthroughdate,
       rpl.borough AS rpl_borough,
       rpl.block AS rpl_block,
       rpl.lot AS rpl_lot,
       rpl.partiallot AS rpl_partiallot,
       rpl.streetnumber AS rpl_streetnumber,
       rpl.streetname AS rpl_streetname,
       rpl.unit AS rpl_unit,
       rpl.goodthroughdate AS rpl_goodthroughdate,
       rpl.bbl AS rpl_bbl,
       CASE
           WHEN rpp.partytype = 1 THEN dcc.party1type
           WHEN rpp.partytype = 2 THEN dcc.party2type
           WHEN rpp.partytype = 3 THEN dcc.party3type
           else rpp.partytype::character(1)
           END
           AS dcc_partytype_desc,
       rpp.name AS rpp_name,
       rpp.address1 AS rpp_address1,
       rpp.address2 AS rpp_address2,
       rpp.country AS rpp_country,
       rpp.city AS rpp_city,
       rpp.state AS rpp_state,
       rpp.zip AS rpp_zip,
       apc.description AS apc_property_description,
       dcc.doctypedescription AS dcc_doctypedescription,
       dcc.classcodedescription AS dcc_classcodedescription
   FROM real_property_master rpm
            JOIN ( SELECT DISTINCT documentid,
                                        borough,
                                        block,
                                        lot,
                                        partiallot,
                                        propertytype,
                                        streetnumber,
                                        streetname,
                                        unit,
                                        goodthroughdate,
                                        bbl
                        FROM real_property_legals
                        where streetnumber is not null and streetname is not null
           ) rpl ON rpm.documentid = rpl.documentid
            LEFT JOIN real_property_parties rpp ON rpm.documentid = rpp.documentid
            LEFT JOIN acris_property_type_codes apc ON rpl.propertytype = apc.propertytype
            LEFT JOIN acris_document_control_codes dcc ON rpm.doctype = dcc.doctype;
