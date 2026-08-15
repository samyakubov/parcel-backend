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
from handlers.property_search.helper_functions.get_building_characteristics import (
    get_building_characteristics,
)
from handlers.property_search.helper_functions.get_complaints import (
    get_complaints,
)
from handlers.property_search.helper_functions.get_job_filings import (
    get_job_filings,
)
from handlers.property_search.helper_functions.get_last_sold import (
    get_last_sold,
)
from handlers.property_search.helper_functions.get_mortgage import get_mortgage
from handlers.property_search.helper_functions.get_owners import get_owners
from handlers.property_search.helper_functions.get_zoning import get_zoning
from handlers.property_search.helper_functions.standardize_address_for_database import (
    standardize_address,
)
from logger_config import logger
from schemas import COOP_PROPERTY_TYPES, PropertyDetailsResponse, Violation
from services.geolocation.address_to_coord import address_to_coord


def search_by_property_bbl(
    bbl: str, db: DatabaseConnector, record_filter: list[str] | None = None
) -> PropertyDetailsResponse:
    """Searches for a property by its BBL.

    Args:
        bbl (str): The BBL of the property to search for.
        db (DatabaseConnector): The database connector instance.
        record_filter (list[str] | None): Optional list of doc_type values to restrict the
            returned `records` field to. Applied only to the final records output, not to any
            of the intermediate dataframes used to derive owners, last_sold, mortgage, or
            building_characteristics.

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
        records_df = db.execute_df("SELECT * FROM aggregated_acris_records WHERE bbl = ? ORDER BY documentid", [bbl])

        if records_df.empty:
            logger.warning(f"No records found for BBL: '{bbl}'")
            raise BBLNotFoundError(f"No records found for BBL: {bbl}")

        if "search_prop_address" in records_df.columns:
            records_df = records_df.drop(columns=["search_prop_address"])

        prop_type = records_df.iloc[0].prop_type
        logger.info(f"Found {len(records_df)} records for BBL '{bbl}' with property type '{prop_type}'.")

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

        pluto_df = db.execute_df("SELECT * FROM pluto_latest WHERE bbl = ?", [bbl])

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

        owners, should_get_last_sold_for_buildings = get_owners(bbl, records_df, jobs_df)

        coordinates = None
        if future_coords:
            try:
                coordinates = future_coords.result(timeout=5)
            except Exception as e:
                logger.warning(f"Failed to get coordinates for BBL '{bbl}': {e}")

        executor.shutdown(wait=False)

        last_sold = get_last_sold(bbl, sales_df, records_df, pluto_df) if prop_type not in COOP_PROPERTY_TYPES else None
        building_characteristics = get_building_characteristics(records_df, pluto_df)

        output_records_df = records_df.sort_values(by="record_filed", ascending=False)
        if record_filter:
            output_records_df = output_records_df[output_records_df["doc_type"].isin(record_filter)]

        return PropertyDetailsResponse(
            last_sold = last_sold if prop_type not in COOP_PROPERTY_TYPES or should_get_last_sold_for_buildings else None,
            owners=owners,
            mortgage=get_mortgage(records_df, last_sold),
            building_characteristics=building_characteristics,
            records=output_records_df.to_dict(orient="records"),
            job_filings=get_job_filings(bbl, jobs_df),
            violations=[Violation(**row) for row in violations_df.to_dict(orient="records")],
            complaints=get_complaints(records_df.iloc[0].prop_streetnumber + " " + records_df.iloc[0].prop_streetname, complaints_df),
            zoning=get_zoning(bbl, zoning_df),
            coordinates=coordinates,
        )
    except (InvalidBBLError, BBLNotFoundError) as e:
        logger.warning(f"{type(e).__name__} occurred while searching for BBL '{bbl}': {e}")
        raise
