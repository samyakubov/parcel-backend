from database_connector import DatabaseConnector
from exceptions.party_search_exceptions import (
    InvalidPartyNameError,
    PartyNotFoundError,
)
from logger_config import logger
from pydantic_models import PartySearchResponse, PartyContact, PropertyOwnership, CoParty, PersonProfile
from endpoint_handlers.property_search.search_by_property_bbl import search_by_property_bbl
import re


def _standardize_address(address1: str, city: str, state: str, zip_code: str) -> str:
    """Standardize address components to prevent duplicates from formatting variations.
    
    Args:
        address1: Street address
        city: City name
        state: State code
        zip_code: ZIP code
        
    Returns:
        Standardized address key for grouping
    """ 
    # Normalize address1
    addr = str(address1).upper().strip()
    
    # Skip if completely empty
    if not addr or addr == 'NONE':
        addr = ''
    else:
        # Remove extra spaces
        addr = re.sub(r'\s+', ' ', addr)
        
        # Normalize street number spacing (e.g., "80-44" and "8044" should match)
        # Pattern: number-number at start of address
        addr = re.sub(r'^(\d+)-(\d+)\s+', r'\1\2 ', addr)
        
        # Standardize common street type abbreviations
        addr = addr.replace(' STREET', ' ST')
        addr = addr.replace(' AVENUE', ' AVE')
        addr = addr.replace(' ROAD', ' RD')
        addr = addr.replace(' BOULEVARD', ' BLVD')
        addr = addr.replace(' DRIVE', ' DR')
        addr = addr.replace(' LANE', ' LN')
        addr = addr.replace(' COURT', ' CT')
        addr = addr.replace(' PLACE', ' PL')
        
        # Normalize ordinal street names (e.g., "71ST" and "71" should match)
        # Pattern: number followed by ST/ND/RD/TH
        addr = re.sub(r'(\d+)(?:ST|ND|RD|TH)\b', r'\1', addr)
        
        # Standardize city abbreviations
        addr = addr.replace('BKLYN', 'BROOKLYN')
    
    # Normalize city - ignore city name variations for same street address
    # Many NYC addresses have multiple valid city names (e.g., QUEENS VILLAGE vs HOLLIS HILLS)
    city_norm = str(city).upper().strip()
    if city_norm in ('NONE', ''):
        city_norm = ''
    else:
        city_norm = re.sub(r'\s+', ' ', city_norm)
        # For NYC, use borough-level grouping instead of neighborhood names
        # This prevents duplicates from neighborhood variations
        if city_norm in ('QUEENS VILLAGE', 'HOLLIS HILLS', 'KEW GARDENS HILLS', 'FLUSHING', 'JAMAICA'):
            city_norm = 'QUEENS'
        elif city_norm in ('BROOKLYN', 'BKLYN'):
            city_norm = 'BROOKLYN'
    
    # Normalize state
    state_norm = str(state).upper().strip()
    if state_norm == 'NONE':
        state_norm = ''
    
    # Normalize zip (remove invalid zips like 00000, None, nan, and malformed zips)
    zip_norm = str(zip_code).strip()
    if zip_norm in ('00000', 'None', 'nan', '') or len(zip_norm) > 5:
        zip_norm = ''
    
    # If everything is empty, return a special marker
    if not addr and not city_norm and not state_norm and not zip_norm:
        return 'UNKNOWN'
    
    return f"{addr}|{city_norm}|{state_norm}|{zip_norm}"


def search_by_party_name(last_name: str, first_name: str, db: DatabaseConnector) -> PartySearchResponse:
    """Searches for comprehensive information about a party by name, grouped by individual person.

    Args:
        last_name (str): The last name of the party.
        first_name (str): The first name of the party.
        db (DatabaseConnector): The database connector instance.

    Returns:
        PartySearchResponse: A response object containing profiles for each distinct person found.

    Raises:
        InvalidPartyNameError: If the first or last name is missing.
        PartyNotFoundError: If no records are found for the given party name.
    """
    if not last_name or not first_name:
        logger.warning("Search by party name was called without a last name or first name.")
        raise InvalidPartyNameError("Both first and last name are required.")

    try:
        party_name_records = f"{last_name.upper()}, {first_name.upper()}"
        logger.info(f"Searching for party name: '{party_name_records}'")

        # 1. Get all ACRIS records for this party name
        all_acris_df = db.execute_df(
            "SELECT * FROM aggregated_acris_records WHERE UPPER(party_name) = UPPER(?)",
            [party_name_records],
        )

        if all_acris_df.empty:
            logger.info(f"No ACRIS records found for party name: '{party_name_records}'")
            raise PartyNotFoundError(f"No records found matching the party name: {last_name}, {first_name}")

        logger.info(f"Found {len(all_acris_df)} ACRIS records for party name: '{party_name_records}'")

        # 2. Group by unique address to identify distinct individuals
        # Standardize addresses to prevent duplicates from formatting variations
        all_acris_df['address_key'] = all_acris_df.apply(
            lambda row: _standardize_address(
                row.get('party_address1', ''),
                row.get('party_city', ''),
                row.get('party_state', ''),
                row.get('party_zip', '')
            ),
            axis=1
        )

        # Group by address
        address_groups = all_acris_df.groupby('address_key')
        logger.info(f"Found {len(address_groups)} distinct persons based on unique addresses")

        persons = []
        unknown_counter = 1

        for address_key, group_df in address_groups:
            # 3. Build identifier and primary address
            # Check if this is an unknown address group
            if address_key == 'UNKNOWN':
                identifier = f"Unknown-{unknown_counter}"
                primary_address = None
                unknown_counter += 1
            else:
                # Parse the standardized address_key back to display format
                first_row = group_df.iloc[0]
                
                # Get and validate ZIP code
                zip_val = str(first_row.get('party_zip', '')).strip()
                if zip_val in ('None', 'nan', '00000', '') or len(zip_val) > 5:
                    zip_val = ''
                
                addr_parts = [
                    str(first_row.get('party_address1', '')).strip(),
                    str(first_row.get('party_city', '')).strip(),
                    str(first_row.get('party_state', '')).strip(),
                    zip_val
                ]
                
                # Filter out empty parts and 'None' strings
                addr_parts_clean = [p for p in addr_parts if p and p not in ('None', 'nan', '')]
                
                if addr_parts_clean:
                    identifier = ', '.join(addr_parts_clean)
                    primary_address = identifier
                else:
                    identifier = f"Unknown-{unknown_counter}"
                    primary_address = None
                    unknown_counter += 1

            # 4. Extract contact info for this person
            addresses = []
            for _, row in group_df.iterrows():
                addr_parts = [
                    str(row.get("party_address1", "")).strip(),
                    str(row.get("party_address2", "")).strip(),
                    str(row.get("party_city", "")).strip(),
                    str(row.get("party_state", "")).strip(),
                    str(row.get("party_zip", "")).strip(),
                ]
                addr = ", ".join([p for p in addr_parts if p and p != ""])
                if addr and addr not in addresses:
                    addresses.append(addr)

            contact_info = PartyContact(addresses=addresses)


            # 6. Get phone numbers and business names from DOB Jobs
            first_name_base = first_name.split()[0]
            dob_jobs_df = db.execute_df(
                """
                SELECT DISTINCT OwnersPhone, OwnersBusinessName
                FROM dobjobs 
                WHERE UPPER(ownername) LIKE ?
                AND UPPER(ownername) LIKE ?
                AND (OwnersPhone IS NOT NULL OR OwnersBusinessName IS NOT NULL)
                """,
                [f"%{last_name.upper()}%", f"%{first_name_base.upper()}%"]
            )
            
            if not dob_jobs_df.empty:
                phones = dob_jobs_df["OwnersPhone"].dropna().unique().tolist()
                businesses = dob_jobs_df["OwnersBusinessName"].dropna().unique().tolist()
                contact_info.phone_numbers = [str(p) for p in phones if p]
                contact_info.business_names = [str(b) for b in businesses if b and b != "N/A"]

            # 7. Get full property details for each BBL
            properties = []
            for bbl in group_df["bbl"].dropna().unique():
                try:
                    logger.info(f"Fetching property details for BBL: {bbl}")
                    property_details = search_by_property_bbl(str(bbl), db)
                    properties.append(property_details)
                except Exception as e:
                    logger.warning(f"Failed to fetch property details for BBL {bbl}: {e}")
                    # Skip this property if we can't fetch details
                    continue

            # 8. Find co-parties ONLY from buyer records for this person
            # Filter to only documents where this person was a buyer
            buyer_docs = group_df[group_df['partytype_desc'].str.upper().str.contains('BUYER|GRANTEE', na=False, regex=True)]
            buyer_document_ids = buyer_docs['documentid'].unique().tolist()
            
            co_parties = []
            if buyer_document_ids:
                placeholders_buyer = ", ".join(["?"] * len(buyer_document_ids))
                coparties_df = db.execute_df(
                    f"""
                    SELECT party_name, partytype_desc, COUNT(DISTINCT documentid) as shared_docs
                    FROM aggregated_acris_records
                    WHERE documentid IN ({placeholders_buyer})
                    AND UPPER(party_name) != UPPER(?)
                    GROUP BY party_name, partytype_desc
                    ORDER BY shared_docs DESC
                    LIMIT 20
                    """,
                    buyer_document_ids + [party_name_records]
                )
                
                if not coparties_df.empty:
                    party_groups = coparties_df.groupby("party_name")
                    for party_name, group in party_groups:
                        total_docs = group["shared_docs"].sum()
                        relationship_types = group["partytype_desc"].dropna().unique().tolist()
                        co_parties.append(CoParty(
                            name=str(party_name),
                            shared_document_count=int(total_docs),
                            relationship_types=[str(r) for r in relationship_types if r]
                        ))

            # 9. Create person profile (without records and violations)
            person = PersonProfile(
                identifier=identifier,
                primary_address=primary_address,
                record_count=len(group_df),  # Count of ACRIS records for this person
                contact_info=contact_info,
                properties=properties,
                co_parties=co_parties
            )
            persons.append(person)

        # Sort persons by record count (most active first)
        persons.sort(key=lambda p: p.record_count, reverse=True)

        logger.info(f"Successfully created {len(persons)} person profiles")

        return PartySearchResponse(
            total_persons_found=len(persons),
            persons=persons
        )

    except (InvalidPartyNameError, PartyNotFoundError):
        raise
    except Exception as e:
        logger.error(
            f"An unexpected error occurred while searching for party name '{last_name}, {first_name}': {e}",
            exc_info=True,
        )
        raise
