from fastapi import HTTPException
from starlette import status
from endpoint_handlers.property_search.exceptions import AddressNotFoundException, InvalidAddressException
from endpoint_handlers.property_search.helper_functions.get_building_shareholders import get_building_shareholders
from endpoint_handlers.property_search.helper_functions.get_complaints import get_complaints
from endpoint_handlers.property_search.helper_functions.get_current_home_owner import get_current_home_owner
from endpoint_handlers.property_search.helper_functions.get_job_filings import get_job_filings
from endpoint_handlers.property_search.helper_functions.get_last_sold import get_last_sold
from endpoint_handlers.property_search.helper_functions.get_previous_owners import get_previous_home_owners
from endpoint_handlers.property_search.helper_functions.get_violations import get_violations
from endpoint_handlers.property_search.helper_functions.get_zoning import get_zoning
from logger_config import logger
from services.geolocation.address_to_coord import address_to_coord
from database_connector import db

def search_by_property_address(address: str):
    try:
        if not address:
            logger.error("No address was provided")
            raise InvalidAddressException("Address cannot be empty")

        records_df = db.execute_df("SELECT * FROM aggregated_acris_records WHERE search_prop_address = ? ORDER BY documentid", [address.upper()])
        records_df = records_df.drop(columns=["search_prop_address"])
        current_owner_data = []

        COOP_PROPERTY_TYPES = {
            "MULTIPLE RESIDENTIAL COOP UNIT",
            "APARTMENT BUILDING",
            "SINGLE RESIDENTIAL COOP UNIT"
        }

        if records_df.empty:
            parts = address.strip().split(' ', 1)
            house_number, street = parts
            records_df = db.execute_df("SELECT * FROM aggregated_acris_records WHERE prop_streetnumber = ? AND prop_streetname LIKE ? ORDER BY documentid", [house_number, f"{street.replace(' ', '%').upper()}%"])
            if records_df.empty:
                logger.error("No records found for %s" % address)
                raise AddressNotFoundException(address)

        bbl = records_df.iloc[0].bbl
        prop_type = records_df.iloc[0].prop_type

        if prop_type in COOP_PROPERTY_TYPES:
            current_owner_data = get_building_shareholders(bbl)

        if len(current_owner_data) == 0:
            current_owner_data = get_current_home_owner(bbl)

        all_previous_data = get_previous_home_owners(bbl)
        previous_owner_data = [item for item in all_previous_data if item not in current_owner_data]

        return {
            "last_sold": get_last_sold(records_df.iloc[0].bbl) if records_df.iloc[0].prop_type not in {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"} else [],
            "owners": {
                    "current_owners": current_owner_data,
                    "previous_owners": previous_owner_data,
                },
                "records": records_df.sort_values(by="record_filed", ascending=False).to_dict(orient="records"),
                "job_filings": get_job_filings(records_df.iloc[0].bbl),
                "violations": get_violations(records_df.iloc[0].bbl),
                "complaints": get_complaints(address),
                "zoning": get_zoning(records_df.iloc[0].bbl),
                "coordinates": address_to_coord(address),
                "status_code": 200,
            }
    except (InvalidAddressException, AddressNotFoundException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_by_property_address for address {address}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )