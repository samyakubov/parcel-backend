from concurrent.futures import ThreadPoolExecutor

import pandas as pd

from database_connector import DatabaseConnector
from exceptions.property_search_exceptions import (
    BBLNotFoundError,
    InvalidBBLError,
)
from handlers.property_search.helper_functions.add_ordinal_to_street_number import (
    add_ordinal_to_street_number,
)
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
from handlers.property_search.helper_functions.standardize_address_for_database import (
    standardize_address,
)
from logger_config import logger
from schemas import Owners, PropertyDetailsResponse, Violation
from services.geolocation.address_to_coord import address_to_coord


def search_by_property_bbl(bbl: str, db: DatabaseConnector) -> PropertyDetailsResponse:
    """Searches for a property by its BBL.

    Args:
        bbl (str): The BBL of the property to search for.
        db (DatabaseConnector): The database connector instance.

    Raises:
        InvalidBBLError: If the BBL is invalid.
        BBLNotFoundError: If the BBL is not found.

    Returns:
        dict: A dictionary containing the property information.
    """
    if not bbl:
        logger.warning("An attempt was made to search for a property without providing a BBL.")
        raise InvalidBBLError("BBL cannot be empty")

    executor = ThreadPoolExecutor(max_workers=1)

    try:
        logger.info(f"Starting property search for BBL: '{bbl}'")
        records_df = db.execute_df("SELECT a.*, p.* FROM aggregated_acris_records a LEFT JOIN pluto_latest p ON a.bbl = p.bbl WHERE a.bbl = ? ORDER BY a.documentid", [bbl])
        records_df = records_df.loc[:, ~records_df.columns.duplicated()]

        current_owner_data = []
        should_get_last_sold_for_buildings = False

        coop_property_types = {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}

        if records_df.empty:
            logger.warning(f"No records found for BBL: '{bbl}'")
            raise BBLNotFoundError(f"No records found for BBL: {bbl}")

        if "search_prop_address" in records_df.columns:
            records_df = records_df.drop(columns=["search_prop_address"])

        prop_type = records_df.iloc[0].prop_type
        logger.info(f"Found {len(records_df)} records for BBL '{bbl}' with property type '{prop_type}'.")

        # Parallel geocoding start
        future_coords = None
        try:
            address_str = add_ordinal_to_street_number(
                standardize_address(
                    str(records_df.iloc[0].prop_streetnumber + " " + records_df.iloc[0].prop_streetname).lower()
                )
            )
            future_coords = executor.submit(address_to_coord, address_str)
        except Exception as e:
            logger.warning(f"Failed to prepare address for geocoding BBL '{bbl}': {e}")


        sales_df = db.execute_df("SELECT * FROM aggregated_dof_sales WHERE bbl = ?", [bbl])

        jobs_df = db.execute_df("SELECT * FROM dobjobs WHERE bbl = ?", [bbl])

        violations_df = db.execute_df(
            """SELECT bbl, violation_status, issue_date, violation_type, description, severity, 
                      penalty_amount, amount_paid, balance_due, respondent_name, house_number, street, city, zip 
               FROM aggregated_acris_violations WHERE bbl = ?""",
            [bbl]
        )

        zoning_df = db.execute_df("SELECT * FROM zoning WHERE bbl = ?", [bbl])

        std_street_number = records_df.iloc[0].prop_streetnumber
        std_street_name = records_df.iloc[0].prop_streetname

        complaints_df = pd.DataFrame()
        if std_street_number and std_street_name:
             address_for_complaints = f"{std_street_number} {std_street_name}"

             std_address_complaints = standardize_address(address_for_complaints)
             c_house_num = std_address_complaints.split(" ")[0]
             c_street_name = " ".join(std_address_complaints.split(" ")[1:])

             complaints_df = db.execute_df(
                "SELECT * FROM dob_complaints WHERE housenumber = ? AND housestreet = ?",
                [c_house_num, c_street_name]
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
            logger.info(f"Property type is a CO-OP ('{prop_type}'). Fetching shareholder information for BBL {bbl}.")
            current_owner_data = get_building_shareholders(bbl, records_df)

        #means the building is privately owned and has one owner
        if len(current_owner_data) == 0:
            logger.info(
                f"No shareholder information found or property is not a CO-OP. Fetching current home owner for BBL {bbl}."
            )
            should_get_last_sold_for_buildings = True
            current_owner_data = get_current_home_owner(bbl, records_df, phone_numbers_df)

        all_previous_data = get_previous_home_owners(bbl, records_df, phone_numbers_df)

        owners = Owners(
            current_owners=current_owner_data,
            previous_owners=[item for item in all_previous_data if item not in current_owner_data],
        )

        coordinates = None
        if future_coords:
            try:
                coordinates = future_coords.result(timeout=5)
            except Exception as e:
                logger.warning(f"Failed to get coordinates for BBL '{bbl}': {e}")

        executor.shutdown(wait=False)

        last_sold = get_last_sold(bbl, sales_df, records_df) if prop_type not in coop_property_types else None

        return PropertyDetailsResponse(
            last_sold = last_sold if prop_type not in coop_property_types or should_get_last_sold_for_buildings else None,
            owners=owners,
            mortgage=get_mortgage(records_df, last_sold),
            records=records_df.sort_values(by="record_filed", ascending=False).to_dict(orient="records"),
            job_filings=get_job_filings(bbl, jobs_df),
            violations=[Violation(**row) for row in violations_df.to_dict(orient="records")],
            complaints=get_complaints(records_df.iloc[0].prop_streetnumber + " " + records_df.iloc[0].prop_streetname, complaints_df),
            zoning=get_zoning(bbl, zoning_df),
            coordinates=coordinates,
        )
    except (InvalidBBLError, BBLNotFoundError) as e:
        logger.warning(f"{type(e).__name__} occurred while searching for BBL '{bbl}': {e}")
        raise
