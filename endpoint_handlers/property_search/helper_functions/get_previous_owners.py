from database_connector import db
from logger_config import logger

def get_previous_home_owners(bbl):
    try:
        if not bbl or not isinstance(bbl, str):
            logger.error("Invalid BBL provided. It must be a non-empty string.")
            return []


        deed_records = db.execute("SELECT party_name AS owner_name FROM AcrisPropertyAggregate WHERE bbl = ? AND doc_type = 'DEED' AND partytype_desc IN ('GRANTEE/BUYER', 'GRANTOR/SELLER') RDER BY recordedfiled DESC ", (bbl))

        if not deed_records.empty:
            deed_owners = deed_records["owner_name"].tolist()
            seen = set()
            return [owner for owner in deed_owners if not (owner in seen or seen.add(owner))]

        mortgage_doc = db.execute_df("SELECT documentid FROM AcrisPropertyAggregate WHERE bbl = ? AND doc_type = 'MORTGAGE' GROUP BY documentid, recordedfiled, bbl, doc_type ORDER BY recordedfiled DESC LIMIT 1", (bbl))

        if mortgage_doc:

            mortgage_records = db.execute("SELECT party_name AS owner_name FROM AcrisPropertyAggregate WHERE documentid = ? AND partytype_desc = 'MORTGAGOR/BORROWER'", (mortgage_doc[0][0]))
            if not mortgage_records.empty:
                mortgage_owners = mortgage_records["owner_name"].tolist()
                seen = set()
                return [owner for owner in mortgage_owners if not (owner in seen or seen.add(owner))]

        logger.warning(f"No previous owners found for BBL: {bbl}")
        return []

    except Exception as e:
        logger.error(f"Error in get_previous_home_owners for BBL {bbl}: {e}")
        return []
