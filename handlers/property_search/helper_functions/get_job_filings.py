import pandas as pd
from logger_config import logger
from schemas import JobFiled


def get_job_filings(bbl: str, jobs_df: pd.DataFrame) -> list[JobFiled]:
    """Gets job filings for a given BBL.

    Args:
        bbl (str): The BBL of the property to get job filings for.
        jobs_df (pd.DataFrame): DataFrame containing job filings for the BBL.

    Returns:
        list: A list of dictionaries, where each dictionary is a job filing.
            Returns an empty list if no job filings are found or if an error occurs.
    """
    if not bbl:
        logger.warning("Attempted to get job filings without a BBL.")
        return []
        
    if jobs_df.empty:
        logger.info(f"--------------------No job filings found for BBL: {bbl}--------------------\n")
        return []

    try:
        logger.info(f"--------------------Processing job filings for BBL: {bbl}--------------------")
        
        # Raw columns: jobdescription, bin, jobstatus, jobtype, ApplicantsFirstName, ApplicantsLastName, ApplicantProfessionalTitle
        # Renaming map
        rename_map = {
            "JobDescription": "job_description",
            "jobdescription": "job_description",
            "Bin": "bin",
            "bin": "bin",
            "JobStatus": "job_status",
            "jobstatus": "job_status",
            "JobType": "job_type",
            "jobtype": "job_type",
            "ApplicantsFirstName": "applicant_first_name",
            "ApplicantsLastName": "applicant_last_name",
            "ApplicantProfessionalTitle": "applicant_professional_title",
            # Handle standard naming if the DB column names are different in the DF (e.g. lowercase)
            "applicantsfirstname": "applicant_first_name",
            "applicantslastname": "applicant_last_name",
            "applicantprofessionaltitle": "applicant_professional_title",
        }
        
        # Normalize column names in DF to be safe (optional, but good practice if DuckDB returns lower/mixed)
        # jobs_df.columns = [c.lower() for c in jobs_df.columns] # Let's assume input is correct for now or handle case insensitivity?
        # DuckDB usually returns columns as case-insensitive match or whatever is in DB.
        
        # Create a copy/rename
        df = jobs_df.copy()
        # Rename columns that exist in the map
        df = df.rename(columns=rename_map)
        
        # Filter for only the columns we want in the output
        output_cols = [
            "job_description", "bin", "job_status", "job_type",
            "applicant_first_name", "applicant_last_name", "applicant_professional_title"
        ]
        
        # Only keep columns that are present
        final_cols = [c for c in output_cols if c in df.columns]
        df = df[final_cols]

        logger.info(f"--------------------Found {len(df)} job filings for BBL: {bbl}--------------------\n")
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching job filings for BBL {bbl}: {e}", exc_info=True)
        return []
