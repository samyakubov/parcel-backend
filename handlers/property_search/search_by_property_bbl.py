from database_connector import DatabaseConnector
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
from handlers.property_search.helper_functions.standardize_address_for_database import (
    standardize_address,
)
from exceptions.property_search_exceptions import (
    BBLNotFoundError,
    InvalidBBLError,
)
from logger_config import logger
from schemas import Owners, PropertyDetailsResponse
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
    try:
        logger.info(f"Starting property search for BBL: '{bbl}'")

        # Single ACRIS query by BBL - serves BOTH response records AND all helper functions
        acris_df = db.execute_df(
            "SELECT * FROM aggregated_acris_records WHERE bbl = ?", [bbl]
        )

        if acris_df.empty:
            logger.warning(f"No records found for BBL: '{bbl}'")
            raise BBLNotFoundError(f"No records found for BBL: {bbl}")

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
        should_get_last_sold_for_buildings = False

        coop_property_types = {"MULTIPLE RESIDENTIAL COOP UNIT", "APARTMENT BUILDING", "SINGLE RESIDENTIAL COOP UNIT"}

        logger.info(f"Found {len(acris_df)} records for BBL '{bbl}' with property type '{prop_type}'.")

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
            logger.info(f"Property type is a CO-OP ('{prop_type}'). Fetching shareholder information for BBL {bbl}.")
            current_owner_data = get_building_shareholders(bbl, acris_df)

        #means the building is privately owned and has one owner
        if len(current_owner_data) == 0:
            logger.info(
                f"No shareholder information found or property is not a CO-OP. Fetching current home owner for BBL {bbl}."
            )
            should_get_last_sold_for_buildings = True
            current_owner_data = get_current_home_owner(bbl, acris_df, phone_df)

        all_previous_data = get_previous_home_owners(bbl, acris_df, phone_df)

        owners = Owners(
            current_owners=current_owner_data,
            previous_owners=[item for item in all_previous_data if item not in current_owner_data],
        )

        try:
            address_str = add_ordinal_to_street_number(
                standardize_address(
                    str(acris_df.iloc[0]["prop_streetnumber"] + " " + acris_df.iloc[0]["prop_streetname"]).lower()
                )
            )
            coordinates = address_to_coord(address_str)
        except Exception as e:
            logger.warning(f"Failed to get coordinates for BBL '{bbl}': {e}")
            coordinates = None

        last_sold = get_last_sold(bbl, acris_df, db) if prop_type not in coop_property_types or should_get_last_sold_for_buildings else None

        return PropertyDetailsResponse(
            last_sold=last_sold,
            owners=owners,
            mortgage=get_mortgage(acris_df, last_sold),
            records=records_df.sort_values(by="record_filed", ascending=False).to_dict(orient="records"),
            job_filings=get_job_filings(bbl, dobjobs_df),
            violations=get_violations(bbl, db),
            complaints=get_complaints(acris_df.iloc[0]["prop_streetnumber"] + " " + acris_df.iloc[0]["prop_streetname"], db),
            zoning=get_zoning(bbl, db),
            coordinates=coordinates,
        )
    except (InvalidBBLError, BBLNotFoundError) as e:
        logger.warning(f"{type(e).__name__} occurred while searching for BBL '{bbl}': {e}")
        raise
