from database_connector import DatabaseConnector
from exceptions.property_search_exceptions import (
    AddressNotFoundError,
    InvalidAddressError,
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
from handlers.property_search.helper_functions.get_phone_number_by_bbl import (
    extract_phone_numbers,
)
from handlers.property_search.helper_functions.get_previous_owners import (
    get_previous_home_owners,
)
from handlers.property_search.helper_functions.get_zoning import get_zoning
from handlers.property_search.helper_functions.standardize_address_for_database import standardize_address
from logger_config import logger
from schemas import Coordinates, Owners, PropertyDetailsResponse, Violation
from services.geolocation.address_to_coord import address_to_coord


def search_by_property_address(
    address: str, db: DatabaseConnector, coordinates: Coordinates | None = None
) -> PropertyDetailsResponse:
    """Searches for a property by its address.

    Args:
        address: The address of the property to search for.
        db: The database connector instance.
        coordinates: Optional pre-resolved coordinates (skips forward geocoding when provided).

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

        # Combined BBL lookup + bulk ACRIS fetch in one query (single scan of aggregated_acris_records)
        acris_df = db.execute_df(
            "SELECT * FROM aggregated_acris_records WHERE bbl = (SELECT bbl FROM aggregated_acris_records WHERE search_prop_address = ? LIMIT 1)",
            [address.upper()],
        )

        if acris_df.empty:
            logger.info(f"No exact match found for address '{address}'. Trying a more lenient search.")
            parts = address.strip().split(" ", 1)
            if len(parts) == 2:
                house_number, street = parts
                acris_df = db.execute_df(
                    "SELECT * FROM aggregated_acris_records WHERE bbl = (SELECT bbl FROM aggregated_acris_records WHERE prop_streetnumber = ? AND prop_streetname LIKE ? LIMIT 1)",
                    [house_number, f"{street.replace(' ', '%').upper()}%"],
                )

            if acris_df.empty:
                logger.warning(f"No records found for address: '{address}' after lenient search.")
                raise AddressNotFoundError(f"No records found for address: {address}")

        bbl = acris_df.iloc[0]["bbl"]

        # Small pluto lookup (one row per BBL, fast)
        pluto_df = db.execute_df(
            "SELECT * FROM pluto_latest WHERE bbl = ?", [bbl]
        )

        # Build response records by merging ACRIS + pluto in Python (replaces SQL JOIN)
        if not pluto_df.empty:
            records_df = acris_df.merge(pluto_df, on="bbl", how="left")
        else:
            records_df = acris_df.copy()
        records_df = records_df.drop(columns=["search_prop_address"], errors="ignore")

        prop_type = acris_df.iloc[0]["prop_type"]
        current_owner_data = []

        coop_property_types = {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}

        logger.info(
            f"Found {len(acris_df)} records for address '{address}' with BBL {bbl} and property type '{prop_type}'\n"
        )

        sales_df = db.execute_df("SELECT * FROM aggregated_dof_sales WHERE bbl = ?", [bbl])

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

        # Bulk fetch all dobjobs records for this BBL
        dobjobs_df = db.execute_df(
            """SELECT
                jobdescription as job_description,
                bin as bin,
                jobstatus as job_status,
                jobtype as job_type,
                ApplicantsFirstName as applicant_first_name,
                ApplicantsLastName as applicant_last_name,
                ApplicantProfessionalTitle as applicant_professional_title,
                ownersphone as owners_phone,
                ownersfirstname as owners_first_name,
                ownerslastname as owners_last_name
            FROM dobjobs WHERE bbl = ?""",
            [bbl],
        )

        # Extract phone data from dobjobs
        phone_df = extract_phone_numbers(dobjobs_df)

        if prop_type in coop_property_types:
            current_owner_data = get_building_shareholders(bbl, acris_df)

        if len(current_owner_data) == 0:
            current_owner_data = get_current_home_owner(bbl, acris_df, phone_df)

        all_previous_data = get_previous_home_owners(bbl, acris_df, phone_df)
        owners = Owners(
            current_owners=current_owner_data,
            previous_owners=[item for item in all_previous_data if item not in current_owner_data],
        )

        if coordinates is None:
            try:
                coordinates = address_to_coord(address)
            except Exception as e:
                logger.warning(f"Failed to get coordinates for address '{address}': {e}")
                coordinates = None

        last_sold = get_last_sold(bbl, sales_df, records_df) if prop_type not in coop_property_types else None

        return PropertyDetailsResponse(
            last_sold=last_sold,
            owners=owners,
            mortgage=get_mortgage(records_df, last_sold),
            records=records_df.sort_values(by="record_filed", ascending=False).astype(object).where(records_df.notna(), None).to_dict(orient="records"),
            job_filings=get_job_filings(bbl, dobjobs_df),
            violations=[Violation(**row) for row in violations_df.to_dict(orient="records")],
            complaints=get_complaints(address, complaints_df),
            zoning=get_zoning(bbl, zoning_df),
            coordinates=coordinates,
        )
    except (InvalidAddressError, AddressNotFoundError) as e:
        logger.error(f"{type(e).__name__} occurred while searching for address '{address}': {e}")
        raise
