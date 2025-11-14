from fastapi import HTTPException
from starlette import status
from database_connector import db
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
from services.geolocation.address_to_coord import address_to_coord


def search_by_property_bbl(bbl: str):
    try:
        if not bbl:
            logger.error("No BBL was provided")
            raise InvalidBBLException("BBL cannot be empty")

        records_df = db.execute_df("SELECT * FROM aggregated_acris_records WHERE bbl = ? ORDER BY documentid", [bbl])
        records_df = records_df.drop(columns=["search_prop_address"])
        current_owner_data = []

        COOP_PROPERTY_TYPES = {
            "MULTIPLE RESIDENTIAL COOP UNIT",
            "APARTMENT BUILDING",
            "SINGLE RESIDENTIAL COOP UNIT"
        }

        if records_df.empty:
            logger.error("No records found for the given BBL")
            raise BBLNotFoundException(bbl)

        prop_type = records_df.iloc[0].prop_type

        if prop_type in COOP_PROPERTY_TYPES:
            current_owner_data = get_building_shareholders(bbl)

        if len(current_owner_data) == 0:
            current_owner_data = get_current_home_owner(bbl)

        all_previous_data = get_previous_home_owners(bbl)
        previous_owner_data = [item for item in all_previous_data if item not in current_owner_data]

        return {
            "last_sold": get_last_sold(bbl) if records_df.iloc[0].prop_type not in COOP_PROPERTY_TYPES else [],
            "owners": {
                "current_owners": current_owner_data,
                "previous_owners": previous_owner_data,
            },
            "records": records_df.sort_values(by="record_filed", ascending=False).to_dict(orient="records"),
            "job_filings": get_job_filings(bbl),
            "violations": get_violations(bbl),
            "complaints": get_complaints(records_df.iloc[0].prop_streetnumber + " " + records_df.iloc[0].prop_streetname),
            "coordinates": address_to_coord(add_ordinal_to_street_number(standardize_address(str(records_df.iloc[0].prop_streetnumber + " " + records_df.iloc[0].prop_streetname).lower()))),
            "zoning": get_zoning(bbl),
            "status_code": 200,
        }
    except (InvalidBBLException, BBLNotFoundException):
        raise
    except Exception as e:
        logger.error(f"Unexpected error in search_by_property_bbl for BBL {bbl}: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )