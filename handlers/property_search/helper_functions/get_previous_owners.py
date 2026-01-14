from database_connector import DatabaseConnector
from handlers.property_search.helper_functions.get_phone_number_by_bbl import (
    get_phone_number_by_bbl,
)
from logger_config import logger
from utils.match_phone_numbers_to_owner import match_phone_numbers_to_owner


def get_previous_home_owners(bbl: str, db: DatabaseConnector) -> list[str]:
    """Gets the previous homeowners for a given BBL.

    This function first tries to find the owners from deed documents.
    If no owners are found, it then tries to find the owners from the latest mortgage document.

    Args:
        bbl (str): The BBL of the property to get the previous home owners for.
        db (DatabaseConnector): The database connector instance.

    Returns:
        List[str]: A list of strings, where each string is the owner's name and their phone number.
            Returns an empty list if no owners are found or if an error occurs.
    """
    if not bbl or not isinstance(bbl, str):
        logger.error(f"Invalid BBL provided: '{bbl}'. It must be a non-empty string.")
        return []

    try:
        logger.info(f"--------------------Searching for previous home owners of BBL: {bbl}--------------------")
        deed_records = db.execute_df(
            "SELECT party_name AS owner_name FROM aggregated_acris_records WHERE bbl = ? AND doc_type = 'DEED' AND partytype_desc IN ('GRANTEE/BUYER', 'GRANTOR/SELLER') ORDER BY record_filed DESC ",
            [bbl],
        )
        phone_numbers = get_phone_number_by_bbl(bbl, db)

        if not deed_records.empty:
            logger.info(f"Found {len(deed_records)} deed records for BBL {bbl}")
            deed_owners = deed_records["owner_name"].tolist()
            seen = set()
            unique_owners = [owner for owner in deed_owners if not (owner in seen or seen.add(owner))]
            logger.info(
                f"--------------------Found {len(unique_owners)} unique previous owner(s) from deed records for BBL {bbl}--------------------\n"
            )
            return match_phone_numbers_to_owner(phone_numbers, unique_owners)

        logger.info(f"No previous owners found from deed records for BBL {bbl}")
        mortgage_doc = db.execute_df(
            "SELECT documentid FROM aggregated_acris_records WHERE bbl = ? AND doc_type = 'MORTGAGE' GROUP BY documentid, record_filed, bbl, doc_type ORDER BY record_filed DESC LIMIT 1",
            [bbl],
        )

        if not mortgage_doc.empty:
            logger.info(
                f"Found latest mortgage document with ID {mortgage_doc.iloc[0]['documentid']} for BBL {bbl}. Fetching mortgagor records."
            )
            mortgage_records = db.execute_df(
                "SELECT party_name AS owner_name FROM aggregated_acris_records WHERE documentid = ? AND partytype_desc = 'MORTGAGOR/BORROWER'",
                [mortgage_doc.iloc[0]["documentid"]],
            )
            if not mortgage_records.empty:
                mortgage_owners = mortgage_records["owner_name"].tolist()
                seen = set()
                unique_owners = [owner for owner in mortgage_owners if not (owner in seen or seen.add(owner))]
                logger.info(
                    f"--------------------Found {len(unique_owners)} unique previous owner(s) from mortgage records for BBL {bbl}--------------------\n"
                )
                return match_phone_numbers_to_owner(phone_numbers, unique_owners)

        logger.warning(
            f"--------------------No previous owners could be determined for BBL: {bbl} from available records.--------------------\n"
        )
        return []

    except Exception as e:
        logger.error(
            f"An unexpected error occurred while getting previous home owners for BBL {bbl}: {e}", exc_info=True
        )
        return []
