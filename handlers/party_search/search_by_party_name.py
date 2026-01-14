from database_connector import DatabaseConnector
from handlers.property_search.search_by_property_bbl import search_by_property_bbl
from exceptions.party_search_exceptions import (
    InvalidPartyNameError,
    PartyNotFoundError,
)
from logger_config import logger
from schemas import PartySearchResponse


def search_by_party_name(first_name: str, last_name: str, db: DatabaseConnector) -> PartySearchResponse:
    """Searches for all properties currently associated with a party by name.

    Args:
        first_name (str): The first name of the party.
        last_name (str): The last name of the party.
        db (DatabaseConnector): The database connector instance.

    Returns:
        PartySearchResponse: A response object containing all properties associated with the person.

    Raises:
        InvalidPartyNameError: If the first or last name is missing.
        PartyNotFoundError: If no records are found for the given party name.
    """
    if not last_name or not first_name:
        logger.warning("Search by party name was called without a last name or first name.")
        raise InvalidPartyNameError("Both first and last name are required.")

    try:
        party_name_records = f"{last_name.upper()}, {first_name.upper()}"
        logger.info(f"Searching for party name: '{party_name_records}'")

        all_acris_df = db.execute_df(
            "SELECT * FROM aggregated_acris_records WHERE UPPER(party_name) = UPPER(?)",
            [party_name_records],
        )

        if all_acris_df.empty:
            logger.info(f"No ACRIS records found for party name: '{party_name_records}'")
            raise PartyNotFoundError(f"No records found matching the party name: {last_name}, {first_name}")

        logger.info(f"Found {len(all_acris_df)} ACRIS records for party name: '{party_name_records}'")

        unique_bbls = all_acris_df['bbl'].dropna().unique()
        logger.info(f"Found {len(unique_bbls)} distinct properties (BBLs)")

        properties = []
        for bbl in unique_bbls:
            try:
                logger.info(f"Fetching property details for BBL: {bbl}")
                property_details = search_by_property_bbl(str(bbl), db)
                properties.append(property_details)
            except Exception as e:
                logger.warning(f"Failed to fetch property details for BBL {bbl}: {e}")
                continue

        if not properties:
            logger.warning(f"No property details could be fetched for party: '{party_name_records}'")
            raise PartyNotFoundError(f"No property details found for party name: {last_name}, {first_name}")

        logger.info(f"Successfully fetched {len(properties)} properties")

        return PartySearchResponse(properties=properties)

    except (InvalidPartyNameError, PartyNotFoundError):
        raise
    except Exception as e:
        logger.error(f"Unexpected error searching for party '{last_name}, {first_name}': {e}")
        raise
