import pandas as pd

from logger_config import logger
from utils.match_phone_numbers_to_owner import match_phone_numbers_to_owner


def get_current_home_owner(
    bbl: str, acris_df: pd.DataFrame, phone_numbers_df: pd.DataFrame
) -> list[str]:
    """Gets the current homeowner for a given BBL.

    This function first tries to find the owner from the latest deed document.
    If no owner is found, it then tries to find the owner from the latest mortgage document.

    Args:
        bbl (str): The BBL of the property to get the current homeowner for.
        acris_df (pd.DataFrame): DataFrame containing aggregated ACRIS records for the BBL.
        phone_numbers_df (pd.DataFrame): DataFrame containing phone numbers.

    Returns:
        List[str]: A list of strings, where each string is the owner's name and their phone number.
            Returns an empty list if no owner is found or if an error occurs.
    """
    if not bbl:
        logger.error(f"Invalid BBL provided: '{bbl}'.")
        return []

    if acris_df.empty:
         logger.warning(
            f"--------------------No records found for BBL: {bbl}--------------------\n"
        )
         return []

    try:
        logger.info(f"--------------------Searching for current home owner of BBL: {bbl}--------------------")

        deeds = acris_df[acris_df["doc_type"] == "DEED"].copy()

        if not deeds.empty:
            deeds = deeds.sort_values(by="record_filed", ascending=False)
            latest_deed_doc_id = deeds.iloc[0]["documentid"]

            logger.info(f"Found latest deed document with ID {latest_deed_doc_id} for BBL {bbl}")

            deed_buyers = deeds[
                (deeds["documentid"] == latest_deed_doc_id) &
                (deeds["partytype_desc"] == "GRANTEE/BUYER")
            ]

            if not deed_buyers.empty:
                owners = list(set(deed_buyers["party_name"].tolist()))
                logger.info(
                    f"--------------------Found {len(owners)} owner(s) from deed record for BBL {bbl}--------------------\n"
                )
                return match_phone_numbers_to_owner(phone_numbers_df, owners)

        logger.info(f"No definitive owner found from deed records for BBL {bbl}")

        mortgages = acris_df[acris_df["doc_type"] == "MORTGAGE"].copy()

        if not mortgages.empty:
             mortgages = mortgages.sort_values(by="record_filed", ascending=False)
             latest_mortgage_doc_id = mortgages.iloc[0]["documentid"]

             logger.info(f"Found latest mortgage document with ID {latest_mortgage_doc_id} for BBL {bbl}")

             mortgage_borrowers = mortgages[
                 (mortgages["documentid"] == latest_mortgage_doc_id) &
                 (mortgages["partytype_desc"] == "MORTGAGOR/BORROWER")
             ]

             if not mortgage_borrowers.empty:
                owners = list(set(mortgage_borrowers["party_name"].tolist()))
                logger.info(
                    f"--------------------Found {len(owners)} owner(s) from mortgage record for BBL {bbl}--------------------\n"
                )
                return match_phone_numbers_to_owner(phone_numbers_df, owners)

        logger.warning(
            f"--------------------No current owner could be determined for BBL: {bbl} from available records.--------------------\n"
        )
        return []

    except Exception as e:
        logger.error(f"An unexpected error occurred while getting current home owner for BBL {bbl}: {e}", exc_info=True)
        return []
