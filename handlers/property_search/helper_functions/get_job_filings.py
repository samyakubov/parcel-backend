from database_connector import DatabaseConnector
from logger_config import logger
from schemas import JobFiled


def get_job_filings(bbl: str, db: DatabaseConnector) -> list[JobFiled]:
    """Gets job filings for a given BBL.

    Args:
        bbl (str): The BBL of the property to get job filings for.
        db (DatabaseConnector): The database connector instance.

    Returns:
        list: A list of dictionaries, where each dictionary is a job filing.
            Returns an empty list if no job filings are found or if an error occurs.
    """
    if not bbl:
        logger.warning("Attempted to get job filings without a BBL.")
        return []
    try:
        logger.info(f"--------------------Fetching job filings for BBL: {bbl}--------------------")
        job_filings_df = db.execute_df(
            """SELECT
                                                jobdescription as job_description,
                                                bin as bin,
                                                jobstatus as job_status,
                                                jobtype as job_type,
                                                ApplicantsFirstName as applicant_first_name,
                                                ApplicantsLastName as applicant_last_name,
                                                ApplicantProfessionalTitle as applicant_professional_title
                                          FROM dobjobs WHERE bbl = ?""",
            [bbl],
        )

        if job_filings_df.empty:
            logger.info(f"--------------------No job filings found for BBL: {bbl}--------------------\n")
            return []

        logger.info(f"--------------------Found {len(job_filings_df)} job filings for BBL: {bbl}--------------------\n")
        return job_filings_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching job filings for BBL {bbl}: {e}", exc_info=True)
        return []
