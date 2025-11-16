from typing import Dict, Union, List
from database_connector import DatabaseConnector
from logger_config import logger


def search_by_party_name(last_name: str, first_name: str, db: DatabaseConnector) -> Dict[str, Union[str, int, List]]:
    """Searches for ACRIS records by party name.

    Args:
        last_name (str): The last name of the party.
        first_name (str): The first name of the party.
        db (DatabaseConnector): The database connector instance.

    Returns:
        dict: A dictionary containing the search results or an error message.
    """
    if not last_name or not first_name:
        logger.warning("Search by party name was called without a last name or first name.")
        return {"message": "Both first and last name are required.", "status_code": 400}

    try:
        party_name = f"{last_name.upper()}, {first_name.upper()}"
        logger.info(f"Searching for party name: '{party_name}'")

        doc_id_df = db.execute_df("SELECT DISTINCT documentid FROM aggregated_acris_records WHERE UPPER(party_name) = UPPER(?)", [party_name])

        if doc_id_df.empty:
            logger.info(f"No document IDs found for party name: '{party_name}'")
            return {"message": "No records found matching the party name", "status_code": 404}

        document_ids = doc_id_df["documentid"].tolist()
        logger.info(f"Found {len(document_ids)} document ID(s) for party name: '{party_name}'. Fetching full transaction records.")

        placeholders = ", ".join(["?"] * len(document_ids))
        transactions_df = db.execute_df(f"SELECT * FROM aggregated_acris_records WHERE documentid IN ({placeholders}) ORDER BY documentid", document_ids)

        if transactions_df.empty:
            # This case should ideally not be reached if doc_id_df is not empty, but logging for safety.
            logger.warning(f"Found document IDs for '{party_name}' but failed to retrieve transaction details.")
            return {"message": "Could not retrieve records for the given party name", "status_code": 404}

        logger.info(f"Successfully retrieved {len(transactions_df)} transaction records for party name: '{party_name}'.")
        return {
            "records": transactions_df.fillna(value="").to_dict(orient="records"),
            "status_code": 200,
        }

    except Exception as e:
        logger.error(f"An unexpected error occurred while searching for party name '{last_name}, {first_name}': {e}", exc_info=True)
        return {"message": "An unexpected error has occurred", "status_code": 500}