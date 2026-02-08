import pandas as pd

from logger_config import logger


def extract_phone_numbers(dobjobs_df: pd.DataFrame) -> pd.DataFrame | list:
    """Extracts phone numbers from pre-fetched dobjobs data.

    Args:
        dobjobs_df (pd.DataFrame): Pre-fetched dobjobs records with columns:
            owners_phone, owners_first_name, owners_last_name.

    Returns:
        Union[pd.DataFrame, List]: A DataFrame containing the phone numbers and owner_full_name.
            Returns an empty list if no phone numbers are found or if an error occurs.
    """
    try:
        if dobjobs_df.empty:
            return []

        phone_numbers = dobjobs_df[
            ["owners_phone", "owners_first_name", "owners_last_name"]
        ].drop_duplicates()

        if phone_numbers.empty:
            return []

        phone_numbers = phone_numbers.copy()
        phone_numbers["owner_full_name"] = (
            phone_numbers["owners_last_name"].fillna("") + ", " + phone_numbers["owners_first_name"].fillna("")
        )
        return phone_numbers
    except Exception as e:
        logger.error(f"Error extracting phone numbers: {e}", exc_info=True)
        return []
