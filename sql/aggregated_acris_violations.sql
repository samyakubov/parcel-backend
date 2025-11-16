CREATE OR REPLACE TABLE aggregated_acris_violations AS
SELECT
    bbl,
    bin,
    boro,
    block,
    lot,
    ecbviolationnumber as violation_number,
    ecbviolationstatus as violation_status,
    issuedate as issue_date,
    violationtype as violation_type,
    respondenthousenumber as house_number,
    respondentstreet as street,
    respondentcity as city,
    respondentzip as zip,
    violationdescription as description,
    hearingdate as disposition_date,
    CAST(NULL as VARCHAR) as disposition_comments,
    severity,
    penalityimposed as penalty_amount,
    amountpaid as amount_paid,
    balancedue as balance_due,
    respondentname as respondent_name
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
    issuedate as issue_date,
    violationtype as violation_type,
    housenumber as house_number,
    street,
    CAST(NULL as VARCHAR) as city,
    CAST(NULL as VARCHAR) as zip,
    description,
    dispositiondate as disposition_date,
    dispositioncomments as disposition_comments,
    violationcategory as severity,
    CAST(NULL as FLOAT) as penalty_amount,
    CAST(NULL as FLOAT) as amount_paid,
    CAST(NULL as FLOAT) as balance_due,
    CAST(NULL as VARCHAR) as respondent_name
FROM nycdb.main.dob_violations;


DROP TABLE nycdb.main.ecb_violations;
DROP TABLE nycdb.main.dob_violations;