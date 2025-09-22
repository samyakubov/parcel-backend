from database_connector import db
from logger_config import logger


def get_job_filings(bbl:str):
    try:
        job_filings_df = db.execute("SELECT filing_reason, job_filing_number, work_type, applicant_license_number, permittee_s_license_type, applicant_first_name, applicant_last_name, applicant_business_name, applicant_business_address, work_permit, approved_date, issued_date, job_description, expired_date, estimated_job_costs FROM PulledPermits WHERE bbl = ?", (bbl))

        if job_filings_df.empty:
            return []

        return job_filings_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []