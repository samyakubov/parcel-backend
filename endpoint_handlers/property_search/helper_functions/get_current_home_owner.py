from database_connector import db
from logger_config import logger


def get_current_home_owner(bbl: str):
    try:
        if not bbl or not isinstance(bbl, str):
            logger.error("Invalid BBL provided. It must be a non-empty string.")
            return "Invalid BBL provided. It must be a non-empty string."

        deed_doc = db.execute("SELECT documentid FROM AcrisPropertyAggregate WHERE bbl = ? AND doc_type = 'DEED' GROUP BY documentid, recordedfiledORDER BY recordedfiled DESC LIMIT 1", (bbl))

        if deed_doc:
            deed_records = db.execute_df("SELECT party_name AS current_owner FROM AcrisPropertyAggregate WHERE documentid = ? AND partytype_desc = 'GRANTEE/BUYER' ", (deed_doc[0][0]))
            if not deed_records.empty:
                return list(set(deed_records["current_owner"].tolist()))

        mortgage_doc = db.execute("SELECT documentid FROM AcrisPropertyAggregate WHERE bbl = ? AND doc_type = 'MORTGAGE' GROUP BY documentid, recordedfiled, bbl, doc_type ORDER BY recordedfiled DESC LIMIT 1", (bbl))

        if mortgage_doc:
            mortgage_records = db.execute_df("SELECT party_name AS current_owner FROM AcrisPropertyAggregate WHERE documentid = ? AND partytype_desc = 'MORTGAGOR/BORROWER'", (mortgage_doc[0][0]))
            if not mortgage_records.empty:
                return list(set(mortgage_records["current_owner"].tolist()))

        logger.warning(f"No current owner found for BBL: {bbl}")
        return []

    except (ValueError, Exception) as e:
        logger.error(f"Error in get_current_owner for BBL {bbl}: {e}")
        return []
