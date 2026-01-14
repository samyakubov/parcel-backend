from database_connector import DatabaseConnector
from handlers.property_search.helper_functions.get_phone_number_by_bbl import (
    get_phone_number_by_bbl,
)
from logger_config import logger
from utils.match_phone_numbers_to_owner import match_phone_numbers_to_owner


def get_current_home_owner(bbl: str, db: DatabaseConnector) -> list[str]:
    """Gets the current homeowner for a given BBL.

    This function first tries to find the owner from the latest deed document.
    If no owner is found, it then tries to find the owner from the latest mortgage document.

    Args:
        bbl (str): The BBL of the property to get the current homeowner for.
        db (DatabaseConnector): The database connector instance.

    Returns:
        List[str]: A list of strings, where each string is the owner's name and their phone number.
            Returns an empty list if no owner is found or if an error occurs.
    """
    if not bbl or not isinstance(bbl, str):
        logger.error(f"Invalid BBL provided: '{bbl}'. It must be a non-empty string.")
        return []

    try:
        logger.info(f"--------------------Searching for current home owner of BBL: {bbl}--------------------")
        deed_doc = db.execute(
            "SELECT documentid FROM aggregated_acris_records WHERE bbl = ? AND doc_type = 'DEED' GROUP BY documentid, record_filed ORDER BY record_filed DESC LIMIT 1",
            [bbl],
        )
        phone_numbers = get_phone_number_by_bbl(bbl, db)

        if deed_doc:
            logger.info(f"Found latest deed document with ID {deed_doc[0][0]} for BBL {bbl}")
            deed_records = db.execute_df(
                "SELECT party_name AS current_owner FROM aggregated_acris_records WHERE documentid = ? AND partytype_desc = 'GRANTEE/BUYER' ",
                [deed_doc[0][0]],
            )
            if not deed_records.empty:
                owners = list(set(deed_records["current_owner"].tolist()))
                logger.info(
                    f"--------------------Found {len(owners)} owner(s) from deed record for BBL {bbl}--------------------\n"
                )
                return match_phone_numbers_to_owner(phone_numbers, owners)

        logger.info(f"No definitive owner found from deed records for BBL {bbl}")
        mortgage_doc = db.execute(
            "SELECT documentid FROM aggregated_acris_records WHERE bbl = ? AND doc_type = 'MORTGAGE' GROUP BY documentid, record_filed, bbl, doc_type ORDER BY record_filed DESC LIMIT 1",
            [bbl],
        )

        if mortgage_doc:
            logger.info(f"Found latest mortgage document with ID {mortgage_doc[0][0]} for BBL {bbl}")
            mortgage_records = db.execute_df(
                "SELECT party_name AS current_owner FROM aggregated_acris_records WHERE documentid = ? AND partytype_desc = 'MORTGAGOR/BORROWER'",
                [mortgage_doc[0][0]],
            )
            if not mortgage_records.empty:
                owners = list(set(mortgage_records["current_owner"].tolist()))
                logger.info(
                    f"--------------------Found {len(owners)} owner(s) from mortgage record for BBL {bbl}--------------------\n"
                )
                return match_phone_numbers_to_owner(phone_numbers, owners)

        logger.warning(
            f"--------------------No current owner could be determined for BBL: {bbl} from available records.--------------------\n"
        )
        return []

    except Exception as e:
        logger.error(f"An unexpected error occurred while getting current home owner for BBL {bbl}: {e}", exc_info=True)
        return []
