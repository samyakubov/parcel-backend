import difflib

import pandas as pd

from logger_config import logger
from utils.match_phone_numbers_to_owner import match_phone_numbers_to_owner

NAME_SIMILARITY_THRESHOLD = 0.9


def _dedupe_similar_owners(owners: list[str]) -> list[str]:
    """Dedupes owner names, collapsing near-identical spellings (e.g. typos in source records)."""
    unique: list[str] = []
    for owner in owners:
        if not any(
            difflib.SequenceMatcher(None, owner, existing).ratio() >= NAME_SIMILARITY_THRESHOLD
            for existing in unique
        ):
            unique.append(owner)
    return unique


def get_previous_home_owners(
    bbl: str, acris_df: pd.DataFrame, phone_numbers_df: pd.DataFrame
) -> list[str]:
    """Gets the previous homeowners for a given BBL.

    This function first tries to find the owners from deed documents.
    If no owners are found, it then tries to find the owners from the latest mortgage document.

    Args:
        bbl (str): The BBL of the property to get the previous home owners for.
        acris_df (pd.DataFrame): DataFrame containing aggregated ACRIS records.
        phone_numbers_df (pd.DataFrame): DataFrame containing phone numbers.

    Returns:
        List[str]: A list of strings, where each string is the owner's name and their phone number.
            Returns an empty list if no owners are found or if an error occurs.
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
        logger.info(f"--------------------Analyzing previous home owners of BBL: {bbl}--------------------")

        mask = (
            (acris_df["doc_type"] == 'DEED') &
            (acris_df["partytype_desc"].isin(['GRANTEE/BUYER', 'GRANTOR/SELLER']))
        )
        deed_records = acris_df[mask].sort_values(by="record_filed", ascending=False)

        if not deed_records.empty:
            logger.info(f"Found {len(deed_records)} deed records for BBL {bbl}")
            deed_owners = deed_records["party_name"].tolist()
            unique_owners = _dedupe_similar_owners(deed_owners)
            logger.info(
                f"--------------------Found {len(unique_owners)} unique previous owner(s) from deed records for BBL {bbl}--------------------\n"
            )
            return match_phone_numbers_to_owner(phone_numbers_df, unique_owners)

        logger.info(f"No previous owners found from deed records for BBL {bbl}")

        mask_mortgage = (acris_df["doc_type"] == 'MORTGAGE')
        mortgages = acris_df[mask_mortgage].sort_values(by="record_filed", ascending=False)

        if not mortgages.empty:
            latest_mortgage_doc_id = mortgages.iloc[0]["documentid"]

            logger.info(
                f"Found latest mortgage document with ID {latest_mortgage_doc_id} for BBL {bbl}. Fetching mortgagor records."
            )

            mortgage_records = mortgages[
                 (mortgages["documentid"] == latest_mortgage_doc_id) &
                 (mortgages["partytype_desc"] == "MORTGAGOR/BORROWER")
            ]

            if not mortgage_records.empty:
                mortgage_owners = mortgage_records["party_name"].tolist()
                unique_owners = _dedupe_similar_owners(mortgage_owners)
                logger.info(
                    f"--------------------Found {len(unique_owners)} unique previous owner(s) from mortgage records for BBL {bbl}--------------------\n"
                )
                return match_phone_numbers_to_owner(phone_numbers_df, unique_owners)

        logger.warning(
            f"--------------------No previous owners could be determined for BBL: {bbl} from available records.--------------------\n"
        )
        return []

    except Exception as e:
        logger.error(
            f"An unexpected error occurred while getting previous home owners for BBL {bbl}: {e}", exc_info=True
        )
        return []
