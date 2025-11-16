from fastapi import HTTPException
from starlette import status

from database_connector import DatabaseConnector
from endpoint_handlers.property_search.exceptions import BBLNotFoundException, InvalidBBLException
from endpoint_handlers.property_search.helper_functions.add_ordinal_to_street_number import add_ordinal_to_street_number
from endpoint_handlers.property_search.helper_functions.get_building_shareholders import get_building_shareholders
from endpoint_handlers.property_search.helper_functions.get_complaints import get_complaints
from endpoint_handlers.property_search.helper_functions.get_current_home_owner import get_current_home_owner
from endpoint_handlers.property_search.helper_functions.get_job_filings import get_job_filings
from endpoint_handlers.property_search.helper_functions.get_last_sold import get_last_sold
from endpoint_handlers.property_search.helper_functions.get_previous_owners import get_previous_home_owners
from endpoint_handlers.property_search.helper_functions.get_violations import get_violations
from endpoint_handlers.property_search.helper_functions.get_zoning import get_zoning
from endpoint_handlers.property_search.helper_functions.standardize_address_for_database import standardize_address
from logger_config import logger
from pydantic_models import Owners, PropertyDetailsResponse
from services.geolocation.address_to_coord import address_to_coord


def search_by_property_bbl(bbl: str, db: DatabaseConnector):
    """Searches for a property by its BBL.

    Args:
        bbl (str): The BBL of the property to search for.
        db (DatabaseConnector): The database connector instance.

    Raises:
        InvalidBBLException: If the BBL is invalid.
        BBLNotFoundException: If the BBL is not found.
        HTTPException: If an unexpected error occurs.

    Returns:
        dict: A dictionary containing the property information.
    """
    if not bbl:
        logger.warning("An attempt was made to search for a property without providing a BBL.")
        raise InvalidBBLException("BBL cannot be empty")

    try:
        logger.info(f"Starting property search for BBL: '{bbl}'")
        records_df = db.execute_df("SELECT * FROM aggregated_acris_records WHERE bbl = ? ORDER BY documentid", [bbl])
        records_df = records_df.drop(columns=["search_prop_address"])
        current_owner_data = []

        COOP_PROPERTY_TYPES = {
            "MULTIPLE RESIDENTIAL COOP UNIT",
            "APARTMENT BUILDING",
            "SINGLE RESIDENTIAL COOP UNIT"
        }

        if records_df.empty:
            logger.warning(f"No records found for BBL: '{bbl}'")
            raise BBLNotFoundException(bbl)

        prop_type = records_df.iloc[0].prop_type
        logger.info(f"Found {len(records_df)} records for BBL '{bbl}' with property type '{prop_type}'.")


        if prop_type in COOP_PROPERTY_TYPES:
            logger.info(f"Property type is a CO-OP ('{prop_type}'). Fetching shareholder information for BBL {bbl}.")
            current_owner_data = get_building_shareholders(bbl, db)

        if len(current_owner_data) == 0:
            logger.info(f"No shareholder information found or property is not a CO-OP. Fetching current home owner for BBL {bbl}.")
            current_owner_data = get_current_home_owner(bbl, db)

        all_previous_data = get_previous_home_owners(bbl, db)

        owners = Owners(
            current_owners=current_owner_data,
            previous_owners=[item for item in all_previous_data if item not in current_owner_data],
        )
        return PropertyDetailsResponse(
            last_sold=get_last_sold(bbl, db) if prop_type not in COOP_PROPERTY_TYPES else None,  # Changed [] to None
            owners=owners,
            records=records_df.sort_values(by="record_filed", ascending=False).to_dict(orient="records"),
            job_filings=get_job_filings(bbl, db),
            violations=get_violations(bbl, db),
            complaints=get_complaints(records_df.iloc[0].prop_streetnumber + " " + records_df.iloc[0].prop_streetname, db),
            zoning=get_zoning(bbl, db),
            coordinates= address_to_coord(add_ordinal_to_street_number(standardize_address(str(records_df.iloc[0].prop_streetnumber + " " + records_df.iloc[0].prop_streetname).lower())))
        )
    except (InvalidBBLException, BBLNotFoundException) as e:
        logger.warning(f"{type(e).__name__} occurred while searching for BBL '{bbl}': {e}")
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in search_by_property_bbl for BBL {bbl}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing your request."
        )
