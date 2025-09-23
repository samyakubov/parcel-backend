CREATE OR REPLACE TABLE aggregated_acris_violations AS
SELECT
    bbl,
    bin,
    boro,
    block,
    lot,
    ecbviolationnumber as violation_number,
    ecbviolationstatus as violation_status,
    issuedate,
    violationtype,
    respondenthousenumber as house_number,
    respondentstreet as street,
    respondentcity as city,
    respondentzip as zip,
    violationdescription as description,
    hearingdate as disposition_date,
    CAST(NULL as VARCHAR) as disposition_comments,
    severity,
    penalityimposed as penalty_amount,
    amountpaid,
    balancedue,
    respondentname
FROM nycdb.main.ecb_violations

UNION ALL

SELECT
    bbl,
    bin,
    boro,
    block,
    lot,
    violationnumber as violation_number,
    violationtypecode as violation_status,
    issuedate,
    violationtype,
    housenumber as house_number,
    street,
    CAST(NULL as VARCHAR) as city,
    CAST(NULL as VARCHAR) as zip,
    description,
    dispositiondate as disposition_date,
    dispositioncomments,
    violationcategory as severity,
    CAST(NULL as FLOAT) as penalty_amount,
    CAST(NULL as FLOAT) as amountpaid,
    CAST(NULL as FLOAT) as balancedue,
    CAST(NULL as VARCHAR) as respondentname
FROM nycdb.main.dob_violations;


DROP TABLE nycdb.main.ecb_violations;
DROP TABLE nycdb.main.dob_violations;