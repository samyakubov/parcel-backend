from concurrent.futures import ThreadPoolExecutor
import pandas as pd
from database_connector import DatabaseConnector
from handlers.property_search.helper_functions.standardize_address_for_database import standardize_address
from handlers.property_search.helper_functions.get_building_shareholders import (
    get_building_shareholders,
)
from handlers.property_search.helper_functions.get_complaints import (
    get_complaints,
)
from handlers.property_search.helper_functions.get_current_home_owner import (
    get_current_home_owner,
)
from handlers.property_search.helper_functions.get_job_filings import (
    get_job_filings,
)
from handlers.property_search.helper_functions.get_last_sold import (
    get_last_sold,
)
from handlers.property_search.helper_functions.get_mortgage import get_mortgage
from handlers.property_search.helper_functions.get_previous_owners import (
    get_previous_home_owners,
)
from handlers.property_search.helper_functions.get_zoning import get_zoning
from exceptions.property_search_exceptions import (
    AddressNotFoundError,
    InvalidAddressError,
)
from logger_config import logger
from schemas import Owners, PropertyDetailsResponse, Violation
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

    executor = ThreadPoolExecutor(max_workers=1)
    future_coords = executor.submit(address_to_coord, address)

    try:
        logger.info(
            f"--------------------------Starting property search for address: '{address}'--------------------------"
        )
        records_df = db.execute_df(
            "SELECT a.*, p.* FROM aggregated_acris_records a LEFT JOIN pluto_latest p ON a.bbl = p.bbl WHERE a.search_prop_address = ? ORDER BY a.documentid",
            [address.upper()],
        )
        records_df = records_df.loc[:, ~records_df.columns.duplicated()]

        current_owner_data = []

        coop_property_types = {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}

        if records_df.empty:
            logger.info(f"No exact match found for address '{address}'. Trying a more lenient search.")
            parts = address.strip().split(" ", 1)
            if len(parts) == 2:
                house_number, street = parts
                records_df = db.execute_df(
                    "SELECT a.*, p.* FROM aggregated_acris_records a LEFT JOIN pluto_latest p ON a.bbl = p.bbl WHERE a.prop_streetnumber = ? AND a.prop_streetname LIKE ? ORDER BY a.documentid",
                    [house_number, f"{street.replace(' ', '%').upper()}%"],
                )
                records_df = records_df.loc[:, ~records_df.columns.duplicated()]

            if records_df.empty:
                logger.warning(f"No records found for address: '{address}' after lenient search.")
                raise AddressNotFoundError(f"No records found for address: {address}")

        if "search_prop_address" in records_df.columns:
            records_df = records_df.drop(columns=["search_prop_address"])

        bbl = records_df.iloc[0].bbl
        prop_type = records_df.iloc[0].prop_type
        logger.info(
            f"Found {len(records_df)} records for address '{address}' with BBL {bbl} and property type '{prop_type}'\n"
        )

        sales_df = db.execute_df("SELECT * FROM aggregated_dof_sales WHERE bbl = ?", [bbl])
        
        jobs_df = db.execute_df("SELECT * FROM dobjobs WHERE bbl = ?", [bbl])
        logger.info(f"--------------------Retrieving violations for BBL: {bbl}--------------------")

        violations_df = db.execute_df(
            """SELECT bbl, violation_status, issue_date, violation_type, description, severity, 
                      penalty_amount, amount_paid, balance_due, respondent_name, house_number, street, city, zip 
               FROM aggregated_acris_violations WHERE bbl = ?""", 
            [bbl]
        )
        logger.info(f"--------------------Found {len(violations_df)} violations for BBL: {bbl}--------------------\n")

        zoning_df = db.execute_df("SELECT * FROM zoning WHERE bbl = ?", [bbl])
        
        std_address = standardize_address(address)
        house_num = std_address.split(" ")[0]
        street_name = " ".join(std_address.split(" ")[1:])
        complaints_df = db.execute_df(
            "SELECT * FROM dob_complaints WHERE housenumber = ? AND housestreet = ?", 
            [house_num, street_name]
        )

        phone_numbers_df = pd.DataFrame()
        if not jobs_df.empty:
            potential_cols = {
                "ownername": "owner_full_name", 
                "OwnersPhone": "owners_phone"
            }
            cols_to_use = [c for c in potential_cols.keys() if c in jobs_df.columns]
            if len(cols_to_use) == 2:
                phone_numbers_df = jobs_df[cols_to_use].rename(columns=potential_cols)


        if prop_type in coop_property_types:
            current_owner_data = get_building_shareholders(bbl, records_df)

        if len(current_owner_data) == 0:
            current_owner_data = get_current_home_owner(bbl, records_df, phone_numbers_df)

        all_previous_data = get_previous_home_owners(bbl, records_df, phone_numbers_df)
        owners = Owners(
            current_owners=current_owner_data,
            previous_owners=[item for item in all_previous_data if item not in current_owner_data],
        )

        try:
            coordinates = future_coords.result(timeout=5)
        except Exception as e:
            logger.warning(f"Failed to get coordinates for address '{address}': {e}")
            coordinates = None
        
        executor.shutdown(wait=False)

        last_sold = get_last_sold(bbl, sales_df, records_df) if prop_type not in coop_property_types else None
        
        return PropertyDetailsResponse(
            last_sold=last_sold,
            owners=owners,
            mortgage=get_mortgage(records_df, last_sold),
            records=records_df.sort_values(by="record_filed", ascending=False).to_dict(orient="records"),
            job_filings=get_job_filings(bbl, jobs_df),
            violations=[Violation(**row) for row in violations_df.to_dict(orient="records")],
            complaints=get_complaints(address, complaints_df),
            zoning=get_zoning(bbl, zoning_df),
            coordinates=coordinates,
        )
    except (InvalidAddressError, AddressNotFoundError) as e:
        logger.error(f"{type(e).__name__} occurred while searching for address '{address}': {e}")
        raise
