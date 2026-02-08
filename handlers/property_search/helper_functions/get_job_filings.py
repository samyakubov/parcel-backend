import pandas as pd

from logger_config import logger
from schemas import JobFiled


def get_job_filings(bbl: str, dobjobs_df: pd.DataFrame) -> list[JobFiled]:
    """Gets job filings for a given BBL from pre-fetched dobjobs data.

    Args:
        bbl (str): The BBL of the property to get job filings for.
        dobjobs_df (pd.DataFrame): Pre-fetched dobjobs records for this BBL.

    Returns:
        list: A list of dictionaries, where each dictionary is a job filing.
            Returns an empty list if no job filings are found or if an error occurs.
    """
    if not bbl:
        logger.warning("Attempted to get job filings without a BBL.")
        return []
    try:
        logger.info(f"--------------------Fetching job filings for BBL: {bbl}--------------------")

        if dobjobs_df.empty:
            logger.info(f"--------------------No job filings found for BBL: {bbl}--------------------\n")
            return []

        job_filings_df = dobjobs_df[
            ["job_description", "bin", "job_status", "job_type",
             "applicant_first_name", "applicant_last_name", "applicant_professional_title"]
        ].copy()

        logger.info(f"--------------------Found {len(job_filings_df)} job filings for BBL: {bbl}--------------------\n")
        # Convert object columns to Python-native types so NaN becomes None (not float nan)
        job_filings_df = job_filings_df.astype(object).where(job_filings_df.notna(), None)
        return job_filings_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching job filings for BBL {bbl}: {e}", exc_info=True)
        return []
