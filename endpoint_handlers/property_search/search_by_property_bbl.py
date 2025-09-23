from database_connector import db
from endpoint_handlers.property_search.helper_functions.add_ordinal_to_street_number import add_ordinal_to_street_number
from endpoint_handlers.property_search.helper_functions.get_building_shareholders import get_building_shareholders
from endpoint_handlers.property_search.helper_functions.get_complaints import get_complaint_data
from endpoint_handlers.property_search.helper_functions.get_current_home_owner import get_current_home_owner
from endpoint_handlers.property_search.helper_functions.get_job_filings import get_job_filings
from endpoint_handlers.property_search.helper_functions.get_last_sold import get_last_sold
from endpoint_handlers.property_search.helper_functions.get_previous_owners import get_previous_home_owners
from endpoint_handlers.property_search.helper_functions.get_violations import get_violation_data
from endpoint_handlers.property_search.helper_functions.get_zoning_details import get_zoning_details
from endpoint_handlers.property_search.helper_functions.standardize_address_for_database import standardize_address
from logger_config import logger
from services.geolocation.address_to_coord import address_to_coord


def search_by_property_bbl(bbl: str):
    try:
        if not bbl:
            logger.error("No BBL was provided")
            return {"message": "No BBL was provided", "status_code": 400}

        transactions_df = db.execute_df(" SELECT * FROM vm_acris_index WHERE bbl = ? ORDER BY documentid", [bbl])

        if transactions_df.empty:
            logger.error("No records found for the given BBL")
            return {"message": "No records found for the given BBL", "status_code": 400}


        if transactions_df.iloc[0].prop_type in {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}:
            current_owner_data = get_building_shareholders(bbl)
            previous_owner_data = []
        else:
            current_owner_data = get_current_home_owner(bbl)
            all_previous_data = get_previous_home_owners(transactions_df.iloc[0].bbl)
            previous_owner_data = [item for item in all_previous_data if item not in current_owner_data]

        return {
            "last_sold_for": get_last_sold(bbl),
            "owners": {
                "current_owners": current_owner_data,
                "previous_owners": previous_owner_data,
            },
            "records": transactions_df.sort_values(by="recordedfiled", ascending=False).to_dict(orient="records"),
            "permits": get_job_filings(transactions_df.iloc[0].bbl),
            "violations": get_violation_data(transactions_df.iloc[0].bbl),
            "complaints": get_complaint_data(transactions_df.iloc[0].prop_streetnumber + " " + transactions_df.iloc[0].prop_streetname),
            "coordinates": address_to_coord(add_ordinal_to_street_number(standardize_address(str(transactions_df.iloc[0].prop_streetnumber + " " + transactions_df.iloc[0].prop_streetname).lower()))),
            "zoning": get_zoning_details(bbl),
            "status_code": 200,
        }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"message": "An unexpected error has occurred", "status_code": 500}
