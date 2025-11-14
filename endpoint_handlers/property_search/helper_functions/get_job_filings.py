from database_connector import db
from logger_config import logger


def get_job_filings(bbl:str):
    try:
        job_filings_df = db.execute_df("""SELECT 
                                                jobdescription as job_description, 
                                                bin as bin,
                                                jobstatus as job_status,
                                                jobtype as job_type,
                                                ApplicantsFirstName as applicant_first_name,
                                                ApplicantsLastName as applicant_last_name,
                                                ApplicantProfessionalTitle as applicant_professional_title
                                          FROM dobjobs WHERE bbl = ?""",
                                       [bbl])

        if job_filings_df.empty:
            return []
        return job_filings_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
