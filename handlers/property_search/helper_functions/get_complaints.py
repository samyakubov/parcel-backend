import pandas as pd

from handlers.property_search.helper_functions.standardize_address_for_database import (
    standardize_address,
)
from logger_config import logger
from schemas import Complaint


def get_complaints(address: str, complaints_df: pd.DataFrame) -> list[Complaint]:
    """Gets complaints for a given address.

    Args:
        address: The address to get complaints for.
        complaints_df: DataFrame containing complaints data.

    Returns:
        A list of Complaint objects containing complaint information.
        Returns an empty list if no complaints are found or if an error occurs.
    """
    if not address:
        logger.warning("An attempt was made to get complaints without providing an address.")
        return []

    try:
        logger.info(f"--------------------Analyzing complaints for address: '{address}'--------------------")
        
        # We need to standardize the address to match the query logic, but since we are bulk fetching
        # using the SAME standardized address in the handlers, the dataframe passed in *should*
        # ideally already be filtered for this address OR be the full table (unlikely).
        # Assuming we fetch by address in the main handler, the DF passed here is already filtered.
        # However, looking at the code, it takes `address`.
        
        # If the main handler fetches by address, then `complaints_df` is already the result.
        # We just need to process it.
        
        if complaints_df.empty:
             logger.info(f"No complaints found for address: '{address}'.")
             return []

        # The SQL query selected specific columns and renamed them. We need to do that here or expect raw columns.
        # Let's assume raw columns and rename them to match the schema.
        
        # Raw columns from `dob_complaints`:
        # complaintnumber, dateentered, status, specialdistrict, complaintcategory, 
        # dispositiondate, dispositioncode, inspectiondate, dobrundate, bin, housenumber, housestreet
        
        # Renaming map based on previous SQL
        rename_map = {
            "complaintnumber": "complaint_number",
            "dateentered": "date_entered",
            "status": "status",
            "specialdistrict": "special_district",
            "complaintcategory": "complaint_category",
            "dispositiondate": "disposition_date",
            "dispositioncode": "disposition_code",
            "inspectiondate": "inspection_date",
            "dobrundate": "dobrun_date",
            "bin": "bin"
        }
        
        # Filter columns that exist
        cols_to_keep = [col for col in rename_map.keys() if col in complaints_df.columns]
        df = complaints_df[cols_to_keep].copy()
        df = df.rename(columns=rename_map)

        date_columns = ["date_entered", "disposition_date", "inspection_date", "dobrun_date"]
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%Y-%m-%d")

        if "date_entered" in df.columns:
            df = df.sort_values("date_entered", ascending=False)
            
        logger.info(f"--------------------Found {len(df)} complaints for address: '{address}'--------------------\n")
        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while retrieving complaints for address '{address}': {e}", exc_info=True
        )
        return []
