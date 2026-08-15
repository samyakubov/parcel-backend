from concurrent.futures import ThreadPoolExecutor

from database_connector import DatabaseConnector
from exceptions.property_search_exceptions import (
    AddressNotFoundError,
    InvalidAddressError,
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
from handlers.property_search.helper_functions.standardize_address_for_database import standardize_address
from logger_config import logger
from schemas import COOP_PROPERTY_TYPES, PropertyDetailsResponse, Violation
from services.geolocation.address_to_coord import address_to_coord


def search_by_property_address(
    address: str, db: DatabaseConnector, record_filter: list[str] | None = None
) -> PropertyDetailsResponse:
    """Searches for a property by its address.

    Args:
        address: The address of the property to search for.
        db: The database connector instance.
        record_filter (list[str] | None): Optional list of doc_type values to restrict the
            returned `records` field to. Applied only to the final records output, not to any
            of the intermediate dataframes used to derive owners, last_sold, mortgage, or
            building_characteristics.

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
            "SELECT * FROM aggregated_acris_records WHERE search_prop_address = ? ORDER BY documentid",
            [address.upper()],
        )

        if records_df.empty:
            logger.info(f"No exact match found for address '{address}'. Trying a more lenient search.")
            parts = address.strip().split(" ", 1)
            if len(parts) == 2:
                house_number, street = parts
                records_df = db.execute_df(
                    "SELECT * FROM aggregated_acris_records WHERE prop_streetnumber = ? AND prop_streetname LIKE ? ORDER BY documentid",
                    [house_number, f"{street.replace(' ', '%').upper()}%"],
                )

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

        pluto_df = db.execute_df("SELECT * FROM pluto_latest WHERE bbl = ?", [bbl])
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

        owners, _ = get_owners(bbl, records_df, jobs_df)

        try:
            coordinates = future_coords.result(timeout=5)
        except Exception as e:
            logger.warning(f"Failed to get coordinates for address '{address}': {e}")
            coordinates = None

        executor.shutdown(wait=False)

        last_sold = get_last_sold(bbl, sales_df, records_df, pluto_df) if prop_type not in COOP_PROPERTY_TYPES else None
        building_characteristics = get_building_characteristics(records_df, pluto_df)

        output_records_df = records_df.sort_values(by="record_filed", ascending=False)
        if record_filter:
            output_records_df = output_records_df[output_records_df["doc_type"].isin(record_filter)]

        return PropertyDetailsResponse(
            last_sold=last_sold,
            owners=owners,
            mortgage=get_mortgage(records_df, last_sold),
            building_characteristics=building_characteristics,
            records=output_records_df.to_dict(orient="records"),
            job_filings=get_job_filings(bbl, jobs_df),
            violations=[Violation(**row) for row in violations_df.to_dict(orient="records")],
            complaints=get_complaints(address, complaints_df),
            zoning=get_zoning(bbl, zoning_df),
            coordinates=coordinates,
        )
    except (InvalidAddressError, AddressNotFoundError) as e:
        logger.error(f"{type(e).__name__} occurred while searching for address '{address}': {e}")
        raise
