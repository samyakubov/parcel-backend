from database_connector import DatabaseConnector
from logger_config import logger


def get_phone_number_by_bbl(bbl:str, db: DatabaseConnector):
    """Gets phone numbers for a given BBL.

    Args:
        bbl (str): The BBL of the property to get phone numbers for.
        db (DatabaseConnector): The database connector instance.

    Returns:
        pandas.DataFrame: A DataFrame containing the phone numbers and names of the owners.
            Returns an empty list if no phone numbers are found or if an error occurs.
    """
    if not bbl:
        logger.warning("Attempted to get phone number without a BBL.")
        return []
    try:
        logger.info(f"Fetching phone numbers for BBL: {bbl}")
        phone_numbers = db.execute_df("SELECT distinct ownersphone as owners_phone, ownersfirstname as owners_first_name, ownerslastname as owners_last_name FROM dobjobs WHERE bbl = ?", [bbl])
        if phone_numbers.empty:
            logger.info(f"No phone numbers found in job filings for BBL: {bbl}")
            return []
        
        logger.info(f"Found {len(phone_numbers)} phone number entries for BBL: {bbl}")
        phone_numbers["owner_full_name"] = phone_numbers["owners_last_name"].fillna('') + ", " + phone_numbers["owners_first_name"].fillna('')
        return phone_numbers
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching phone numbers for BBL {bbl}: {e}", exc_info=True)
        return []