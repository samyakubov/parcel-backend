from database_connector import db
from logger_config import logger


def get_phone_number_by_name(party_name:str):
    """Gets phone numbers for a given party name.

    Args:
        party_name (str): The name of the party to search for.

    Returns:
        pandas.DataFrame: A DataFrame containing the phone numbers and names of the owners.
            Returns an empty list if no phone numbers are found or if an error occurs.
    """
    if not party_name:
        logger.warning("Attempted to get phone number by name without providing a name.")
        return []
    try:
        logger.info(f"Fetching phone numbers for party name like: '{party_name}'")
        phone_numbers = db.execute_df("SELECT distinct ownersphone as owners_phone, ownersfirstname as owners_first_name, ownerslastname as owners_last_name FROM dobjobs WHERE ownername LIKE ?", [f"%{party_name}%"])

        if phone_numbers.empty:
            logger.info(f"No phone numbers found in job filings for party name like: '{party_name}'")
            return []

        logger.info(f"Found {len(phone_numbers)} phone number entries for party name like: '{party_name}'")
        phone_numbers["owner_full_name"] = phone_numbers["owners_last_name"].fillna('') + ", " + phone_numbers["owners_first_name"].fillna('')
        return phone_numbers

    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching phone numbers for party name '{party_name}': {e}", exc_info=True)
        return []