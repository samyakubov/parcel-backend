from database_connector import db
from endpoint_handlers.property_search.helper_functions.get_phone_number_by_bbl import get_phone_number_by_bbl
from logger_config import logger
from utils.match_phone_numbers_to_owner import match_phone_numbers_to_owner


def get_current_home_owner(bbl: str):
    try:
        if not bbl or not isinstance(bbl, str):
            logger.error("Invalid BBL provided. It must be a non-empty string.")
            return "Invalid BBL provided. It must be a non-empty string."

        deed_doc = db.execute("SELECT documentid FROM aggregated_acris_records WHERE bbl = ? AND doc_type = 'DEED' GROUP BY documentid, record_filed ORDER BY record_filed DESC LIMIT 1", [bbl])
        phone_numbers = get_phone_number_by_bbl(bbl)

        if deed_doc:
            deed_records = db.execute_df("SELECT party_name AS current_owner FROM aggregated_acris_records WHERE documentid = ? AND partytype_desc = 'GRANTEE/BUYER' ", [deed_doc[0][0]])
            if not deed_records.empty:
                owners = list(set(deed_records["current_owner"].tolist()))
                return match_phone_numbers_to_owner(phone_numbers, owners)


        mortgage_doc = db.execute("SELECT documentid FROM aggregated_acris_records WHERE bbl = ? AND doc_type = 'MORTGAGE' GROUP BY documentid, record_filed, bbl, doc_type ORDER BY record_filed DESC LIMIT 1", [bbl])

        if mortgage_doc:
            mortgage_records = db.execute_df("SELECT party_name AS current_owner FROM aggregated_acris_records WHERE documentid = ? AND partytype_desc = 'MORTGAGOR/BORROWER'", [mortgage_doc[0][0]])
            if not mortgage_records.empty:
                owners = list(set(mortgage_records["current_owner"].tolist()))
                return match_phone_numbers_to_owner(phone_numbers, owners)


        logger.warning(f"No current owner found for BBL: {bbl}")
        return []

    except (ValueError, Exception) as e:
        logger.error(f"Error in get_current_owner for BBL {bbl}: {e}")
        return []
