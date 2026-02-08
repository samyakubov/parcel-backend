import pandas as pd

from logger_config import logger
from utils.match_phone_numbers_to_owner import match_phone_numbers_to_owner


def get_current_home_owner(bbl: str, acris_df: pd.DataFrame, phone_df: pd.DataFrame | list) -> list[str]:
    """Gets the current homeowner for a given BBL.

    This function first tries to find the owner from the latest deed document.
    If no owner is found, it then tries to find the owner from the latest mortgage document.

    Args:
        bbl (str): The BBL of the property to get the current homeowner for.
        acris_df (pd.DataFrame): Pre-fetched ACRIS records for this BBL.
        phone_df (pd.DataFrame | list): Pre-fetched phone number data.

    Returns:
        List[str]: A list of strings, where each string is the owner's name and their phone number.
            Returns an empty list if no owner is found or if an error occurs.
    """
    if not bbl or not isinstance(bbl, str):
        logger.error(f"Invalid BBL provided: '{bbl}'. It must be a non-empty string.")
        return []

    try:
        logger.info(f"--------------------Searching for current home owner of BBL: {bbl}--------------------")

        # Find latest deed document
        deeds = acris_df[acris_df["doc_type"] == "DEED"].sort_values("record_filed", ascending=False)

        if not deeds.empty:
            latest_doc_id = deeds.iloc[0]["documentid"]
            logger.info(f"Found latest deed document with ID {latest_doc_id} for BBL {bbl}")

            buyers = acris_df[
                (acris_df["documentid"] == latest_doc_id)
                & (acris_df["partytype_desc"] == "GRANTEE/BUYER")
            ]
            if not buyers.empty:
                owners = list(set(buyers["party_name"].tolist()))
                logger.info(
                    f"--------------------Found {len(owners)} owner(s) from deed record for BBL {bbl}--------------------\n"
                )
                return match_phone_numbers_to_owner(phone_df, owners)

        logger.info(f"No definitive owner found from deed records for BBL {bbl}")

        # Fallback to mortgage
        mortgages = acris_df[acris_df["doc_type"] == "MORTGAGE"].sort_values("record_filed", ascending=False)

        if not mortgages.empty:
            latest_doc_id = mortgages.iloc[0]["documentid"]
            logger.info(f"Found latest mortgage document with ID {latest_doc_id} for BBL {bbl}")

            borrowers = acris_df[
                (acris_df["documentid"] == latest_doc_id)
                & (acris_df["partytype_desc"] == "MORTGAGOR/BORROWER")
            ]
            if not borrowers.empty:
                owners = list(set(borrowers["party_name"].tolist()))
                logger.info(
                    f"--------------------Found {len(owners)} owner(s) from mortgage record for BBL {bbl}--------------------\n"
                )
                return match_phone_numbers_to_owner(phone_df, owners)

        logger.warning(
            f"--------------------No current owner could be determined for BBL: {bbl} from available records.--------------------\n"
        )
        return []

    except Exception as e:
        logger.error(f"An unexpected error occurred while getting current home owner for BBL {bbl}: {e}", exc_info=True)
        return []
