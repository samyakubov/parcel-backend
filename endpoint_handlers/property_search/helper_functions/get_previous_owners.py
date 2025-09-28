from database_connector import db
from endpoint_handlers.property_search.helper_functions.get_phone_number_by_bbl import get_phone_number_by_bbl
from logger_config import logger
from utils.match_phone_numbers_to_owner import match_phone_numbers_to_owner


def get_previous_home_owners(bbl:str):
    try:
        if not bbl or not isinstance(bbl, str):
            logger.error("Invalid BBL provided. It must be a non-empty string.")
            return []


        deed_records = db.execute_df("SELECT party_name AS owner_name FROM aggregated_acris_records WHERE bbl = ? AND doc_type = 'DEED' AND partytype_desc IN ('GRANTEE/BUYER', 'GRANTOR/SELLER') ORDER BY record_filed DESC ", [bbl])
        phone_numbers = get_phone_number_by_bbl(bbl)

        if not deed_records.empty:
            deed_owners = deed_records["owner_name"].tolist()
            seen = set()
            return match_phone_numbers_to_owner(phone_numbers, [owner for owner in deed_owners if not (owner in seen or seen.add(owner))])

        mortgage_doc = db.execute_df("SELECT documentid FROM aggregated_acris_records WHERE bbl = ? AND doc_type = 'MORTGAGE' GROUP BY documentid, record_filed, bbl, doc_type ORDER BY record_filed DESC LIMIT 1", [bbl])

        if mortgage_doc.empty:
            mortgage_records = db.execute("SELECT party_name AS owner_name FROM aggregated_acris_records WHERE documentid = ? AND partytype_desc = 'MORTGAGOR/BORROWER'", [mortgage_doc[0][0]])
            if not mortgage_records.empty:
                mortgage_owners = mortgage_records["owner_name"].tolist()
                seen = set()
                return match_phone_numbers_to_owner(phone_numbers, [owner for owner in mortgage_owners if not (owner in seen or seen.add(owner))])

        logger.warning(f"No previous owners found for BBL: {bbl}")
        return []

    except Exception as e:
        logger.error(f"Error in get_previous_home_owners for BBL {bbl}: {e}")
        return []
