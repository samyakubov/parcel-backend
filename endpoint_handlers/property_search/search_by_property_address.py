from endpoint_handlers.property_search.helper_functions.get_building_shareholders import get_building_shareholders
from endpoint_handlers.property_search.helper_functions.get_complaints import get_complaint_data
from endpoint_handlers.property_search.helper_functions.get_current_home_owner import get_current_home_owner
from endpoint_handlers.property_search.helper_functions.get_job_filings import get_job_filings
from endpoint_handlers.property_search.helper_functions.get_last_sold import get_last_sold
from endpoint_handlers.property_search.helper_functions.get_previous_owners import get_previous_home_owners
from endpoint_handlers.property_search.helper_functions.get_violations import get_violation_data
from endpoint_handlers.property_search.helper_functions.get_zoning import get_zoning_data
from logger_config import logger
from services.geolocation.address_to_coord import address_to_coord
from database_connector import db

def search_by_property_address(address: str):
    try:
        if not address:
            logger.error("No address was provided")
            return {"message": "No address was provided", "status_code": 400}

        records_df = db.execute_df("SELECT * FROM aggregated_acris_records WHERE search_prop_address = ? ORDER BY documentid", [address.upper()])
        records_df = records_df.drop(columns=["search_prop_address", "prop_partiallot", "m_goodthroughdate"])

        if records_df.empty:
            parts = address.strip().split(' ', 1)
            house_number, street = parts
            records_df = db.execute_df("SELECT * FROM aggregated_acris_records WHERE prop_streetnumber = ? AND prop_streetname LIKE ? ORDER BY documentid", [house_number, f"{street.replace(' ', '%').upper()}%"])
            if records_df.empty:
                logger.error("No records found for %s" % address)
                return {"message": "No records found", "status_code": 404}


        if records_df.iloc[0].prop_type in {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}:
            current_owner_data = get_building_shareholders(records_df.iloc[0].bbl)
            previous_owner_data = []
        else:
            current_owner_data = get_current_home_owner(records_df.iloc[0].bbl)
            all_previous_data = get_previous_home_owners(records_df.iloc[0].bbl)
            previous_owner_data = [item for item in all_previous_data if item not in current_owner_data]

        return {
            "last_sold_for": get_last_sold(records_df.iloc[0].bbl) if records_df.iloc[0].prop_type not in {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"} else [],
            "owners": {
                    "current_owners": current_owner_data,
                    "previous_owners": previous_owner_data,
                },
                "records": records_df.sort_values(by="recordedfiled", ascending=False).to_dict(orient="records"),
                "job_filings": get_job_filings(records_df.iloc[0].bbl),
                "violations": get_violation_data(records_df.iloc[0].bbl),
                "complaints": get_complaint_data(address),
                "zoning": get_zoning_data(records_df.iloc[0].bbl),
                "coordinates": address_to_coord(address),
                "status_code": 200,
            }
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"message": "An unexpected error has occurred", "status_code": 500}
