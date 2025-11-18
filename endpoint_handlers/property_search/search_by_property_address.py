from database_connector import DatabaseConnector
from endpoint_handlers.property_search.helper_functions.get_building_shareholders import (
    get_building_shareholders,
)
from endpoint_handlers.property_search.helper_functions.get_complaints import (
    get_complaints,
)
from endpoint_handlers.property_search.helper_functions.get_current_home_owner import (
    get_current_home_owner,
)
from endpoint_handlers.property_search.helper_functions.get_job_filings import (
    get_job_filings,
)
from endpoint_handlers.property_search.helper_functions.get_last_sold import (
    get_last_sold,
)
from endpoint_handlers.property_search.helper_functions.get_previous_owners import (
    get_previous_home_owners,
)
from endpoint_handlers.property_search.helper_functions.get_violations import (
    get_violations,
)
from endpoint_handlers.property_search.helper_functions.get_zoning import get_zoning
from exceptions.property_search_exceptions import (
    AddressNotFoundError,
    InvalidAddressError,
)
from logger_config import logger
from pydantic_models import Owners, PropertyDetailsResponse
from services.geolocation.address_to_coord import address_to_coord


def search_by_property_address(address: str, db: DatabaseConnector) -> PropertyDetailsResponse:
    """Searches for a property by its address.

    Args:
        address: The address of the property to search for.
        db: The database connector instance.

    Raises:
        InvalidAddressError: If the address is invalid.
        AddressNotFoundError: If the address is not found.
        HTTPException: If an unexpected error occurs.

    Returns:
        PropertyDetailsResponse: A response object containing the property information including
            last sold data, current and previous owners, records, job filings, violations,
            complaints, zoning information, and coordinates.
    """
    if not address:
        logger.warning("An attempt was made to search for a property without providing an address.")
        raise InvalidAddressError("Address cannot be empty")

    try:
        logger.info(
            f"--------------------------Starting property search for address: '{address}'--------------------------"
        )
        records_df = db.execute_df(
            "SELECT * FROM aggregated_acris_records WHERE search_prop_address = ? ORDER BY documentid",
            [address.upper()],
        )
        records_df = records_df.drop(columns=["search_prop_address"])
        current_owner_data = []

        coop_property_types = {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}

        if records_df.empty:
            logger.info(f"No exact match found for address '{address}'. Trying a more lenient search.")
            parts = address.strip().split(" ", 1)
            house_number, street = parts
            records_df = db.execute_df(
                "SELECT * FROM aggregated_acris_records WHERE prop_streetnumber = ? AND prop_streetname LIKE ? ORDER BY documentid",
                [house_number, f"{street.replace(' ', '%').upper()}%"],
            )
            if records_df.empty:
                logger.warning(f"No records found for address: '{address}' after lenient search.")
                raise AddressNotFoundError(f"No records found for address: {address}")

        bbl = records_df.iloc[0].bbl
        prop_type = records_df.iloc[0].prop_type
        logger.info(
            f"Found {len(records_df)} records for address '{address}' with BBL {bbl} and property type '{prop_type}'\n"
        )

        if prop_type in coop_property_types:
            current_owner_data = get_building_shareholders(bbl, db)

        if len(current_owner_data) == 0:
            current_owner_data = get_current_home_owner(bbl, db)

        all_previous_data = get_previous_home_owners(bbl, db)
        owners = Owners(
            current_owners=current_owner_data,
            previous_owners=[item for item in all_previous_data if item not in current_owner_data],
        )

        try:
            coordinates = address_to_coord(address)
        except Exception as e:
            logger.warning(f"Failed to get coordinates for address '{address}': {e}")
            coordinates = None

        return PropertyDetailsResponse(
            last_sold=get_last_sold(bbl, db) if prop_type not in coop_property_types else None,
            owners=owners,
            records=records_df.sort_values(by="record_filed", ascending=False).to_dict(orient="records"),
            job_filings=get_job_filings(bbl, db),
            violations=get_violations(bbl, db),
            complaints=get_complaints(address, db),
            zoning=get_zoning(bbl, db),
            coordinates=coordinates,
        )

    except (InvalidAddressError, AddressNotFoundError) as e:
        logger.error(f"{type(e).__name__} occurred while searching for address '{address}': {e}")
        raise
