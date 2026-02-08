from database_connector import DatabaseConnector
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
from handlers.property_search.helper_functions.get_violations import (
    get_violations,
)
from handlers.property_search.helper_functions.get_zoning import get_zoning
from exceptions.property_search_exceptions import (
    AddressNotFoundError,
    InvalidAddressError,
)
from logger_config import logger
from schemas import Owners, PropertyDetailsResponse
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

    try:
        logger.info(
            f"--------------------------Starting property search for address: '{address}'--------------------------"
        )
        records_df = db.execute_df(
            "SELECT a.*, p.* FROM aggregated_acris_records a LEFT JOIN pluto_latest p ON a.bbl = p.bbl WHERE a.search_prop_address = ? ORDER BY a.documentid",
            [address.upper()],
        )
        records_df = records_df.drop(columns=["search_prop_address"])
        current_owner_data = []

        coop_property_types = {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}

        if records_df.empty:
            logger.info(f"No exact match found for address '{address}'. Trying a more lenient search.")
            parts = address.strip().split(" ", 1)
            house_number, street = parts
            records_df = db.execute_df(
                "SELECT a.*, p.* FROM aggregated_acris_records a LEFT JOIN pluto_latest p ON a.bbl = p.bbl WHERE a.prop_streetnumber = ? AND a.prop_streetname LIKE ? ORDER BY a.documentid",
                [house_number, f"{street.replace(' ', '%').upper()}%"],
            )
            if records_df.empty:
                logger.warning(f"No records found for address: '{address}' after lenient search.")
                raise AddressNotFoundError(f"No records found for address: {address}")

        bbl = records_df.iloc[0].bbl
        prop_type = records_df.iloc[0].prop_type
        logger.info(
            f"Found {len(records_df)} records for address '{address}' with BBL {bbl} and property type '{prop_type}'\n"
        )

        # Bulk fetch all ACRIS records for this BBL (replaces ~10 individual queries)
        acris_df = db.execute_df(
            "SELECT * FROM aggregated_acris_records WHERE bbl = ?", [bbl]
        )

        # Bulk fetch all dobjobs records for this BBL (replaces 3 individual queries)
        dobjobs_df = db.execute_df(
            """SELECT
                jobdescription as job_description,
                bin,
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

        # Extract phone data from dobjobs (previously queried twice separately)
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

        try:
            coordinates = address_to_coord(address)
        except Exception as e:
            logger.warning(f"Failed to get coordinates for address '{address}': {e}")
            coordinates = None

        last_sold = get_last_sold(bbl, acris_df, db) if prop_type not in coop_property_types else None
        return PropertyDetailsResponse(
            last_sold=last_sold,
            owners=owners,
            mortgage=get_mortgage(acris_df, last_sold),
            records=records_df.sort_values(by="record_filed", ascending=False).to_dict(orient="records"),
            job_filings=get_job_filings(bbl, dobjobs_df),
            violations=get_violations(bbl, db),
            complaints=get_complaints(address, db),
            zoning=get_zoning(bbl, db),
            coordinates=coordinates,
        )

    except (InvalidAddressError, AddressNotFoundError) as e:
        logger.error(f"{type(e).__name__} occurred while searching for address '{address}': {e}")
        raise
