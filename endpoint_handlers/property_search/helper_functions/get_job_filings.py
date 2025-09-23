from database_connector import db
from logger_config import logger


def get_job_filings(bbl:str):
    try:
        job_filings_df = db.execute_df("SELECT jobdescription as job_description, ownersphone as owners_phone, jobtype as  job_type, jobstatus as job_status FROM dobjobs WHERE bbl = ?", [bbl])

        if job_filings_df.empty:
            return []

        return job_filings_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []