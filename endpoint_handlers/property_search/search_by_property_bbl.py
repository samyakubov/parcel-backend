from sqlalchemy.exc import SQLAlchemyError
from App.DB.Models.AcrisPropertyAggregate import AcrisPropertyAggregate
from App.DB.Session import session_scope
import pandas as pd
from App.EndpointHandlers.HelperFunctions.CleanResponseDataframe import clean_response_dataframe
from App.EndpointHandlers.HelperFunctions.Geolocation.AddressToCoord import address_to_coord
from App.EndpointHandlers.HelperFunctions.PropertyDetails.AddOrdinalToStreetNumber import add_ordinal_to_street_number
from App.EndpointHandlers.HelperFunctions.PropertyDetails.GetBuildingShareholders import get_building_shareholders
from App.EndpointHandlers.HelperFunctions.PropertyDetails.GetComplaints import get_complaint_data
from App.EndpointHandlers.HelperFunctions.PropertyDetails.GetLastSold import get_last_sold
from App.EndpointHandlers.HelperFunctions.PropertyDetails.GetCurrentHomeOwner import get_current_home_owner
from App.EndpointHandlers.HelperFunctions.PropertyDetails.GetPreviousOwners import get_previous_home_owners
from App.EndpointHandlers.HelperFunctions.PropertyDetails.GetPulledPermits import get_pulled_permits
from App.EndpointHandlers.HelperFunctions.PropertyDetails.GetViolations import get_violation_data
from App.EndpointHandlers.HelperFunctions.PropertyDetails.GetZoningDetails import get_zoning_details
from App.EndpointHandlers.HelperFunctions.PropertyDetails.StandardizeAddressForDatabase import standardize_address
from App.LoggerConfig import logger

def search_by_property_BBL(bbl: str, limit: int):
    try:
        with session_scope() as db_session:
            if not bbl:
                logger.error("No BBL was provided")
                return {"message": "No BBL was provided", "status_code": 400}
            if limit <= 0:
                logger.error("Limit must be a positive integer")
                return {"message": "Limit must be a positive integer", "status_code": 400}

            query = db_session.query(AcrisPropertyAggregate). \
                filter(AcrisPropertyAggregate.bbl == bbl). \
                order_by(AcrisPropertyAggregate.documentid). \
                limit(limit)

            transactions_df = pd.read_sql(query.statement, db_session.bind)
            if transactions_df.empty:
                logger.error("No records found for the given BBL")
                return {"message": "No records found for the given BBL", "status_code": 400}

            clean_response_dataframe(transactions_df)

            if transactions_df.iloc[0].prop_type in {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}:
                current_owner_data =get_building_shareholders(bbl)
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
                "permits": get_pulled_permits(transactions_df.iloc[0].bbl),
                "violations": get_violation_data(transactions_df.iloc[0].bbl),
                "complaints": get_complaint_data(transactions_df.iloc[0].prop_streetnumber + " " + transactions_df.iloc[0].prop_streetname),
                "coordinates": address_to_coord(add_ordinal_to_street_number(standardize_address(str(transactions_df.iloc[0].prop_streetnumber + " " + transactions_df.iloc[0].prop_streetname).lower()))),
                "zoning": get_zoning_details(bbl),
                "status_code": 200,
            }
    except SQLAlchemyError as e:
        logger.error(f"Database error: {e}")
        return {"message": f"Database error: {e}", "status_code": 500}
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"message": "An unexpected error has occurred", "status_code": 500}
