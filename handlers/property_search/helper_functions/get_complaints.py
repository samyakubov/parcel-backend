import pandas as pd

from database_connector import DatabaseConnector
from handlers.property_search.helper_functions.standardize_address_for_database import (
    standardize_address,
)
from logger_config import logger
from schemas import Complaint


def get_complaints(address: str, db: DatabaseConnector) -> list[Complaint]:
    """Gets complaints for a given address.

    Args:
        address: The address to get complaints for.
        db: The database connector instance.

    Returns:
        A list of Complaint objects containing complaint information.
        Returns an empty list if no complaints are found or if an error occurs.
    """
    if not address:
        logger.warning("An attempt was made to get complaints without providing an address.")
        return []

    try:
        logger.info(f"--------------------Fetching complaints for address: '{address}'--------------------")
        standardized_addr = standardize_address(address)
        parts = standardized_addr.strip().split(" ", 1)
        if len(parts) != 2:
            logger.warning(f"Could not parse standardized address '{standardized_addr}' into house number and street.")
            return []

        house_number, street = parts
        street = street.strip().upper()

        logger.info(f"Searching for complaints for house number '{house_number}' and street '{street}'.")
        df = db.execute_df(
            """SELECT
                                  complaintnumber as complaint_number,
                                  dateentered as date_entered,
                                  status as status,
                                  specialdistrict as special_district,
                                  complaintcategory as complaint_category,
                                  dispositiondate as disposition_date,
                                  dispositioncode as disposition_code,
                                  inspectiondate as inspection_date,
                                  dobrundate as dobrun_date,
                                  bin as bin
                              FROM dob_complaints
                              WHERE housenumber = ?
                                AND housestreet LIKE ?
                              ORDER BY dateentered DESC""",
            [str(house_number), f"{street}%"],
        )
        if df.empty:
            logger.info(f"No complaints found for address: '{address}'.")
            return []

        date_columns = ["date_entered", "disposition_date", "inspection_date", "dobrun_date"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

        df = df.sort_values("date_entered", ascending=False)
        logger.info(f"--------------------Found {len(df)} complaints for address: '{address}'--------------------\n")
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while retrieving complaints for address '{address}': {e}", exc_info=True
        )
        return []
