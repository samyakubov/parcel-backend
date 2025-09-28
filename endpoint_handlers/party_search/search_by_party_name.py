from logger_config import logger
from database_connector import db


def search_by_party_name(last_name: str, first_name: str):
    try:
        if not last_name or not first_name:
            logger.error("No party name was provided")
            return {"message": "No party name was provided", "status_code": 400}

        party_name = f"{last_name.upper()}, {first_name.upper()}"
        doc_id_df = db.execute_df("SELECT DISTINCT documentid, party_name FROM aggregated_acris_records WHERE UPPER(party_name) = UPPER(?)", [party_name])

        if 'party_name' not in doc_id_df.columns:
            logger.error("`party_name` column is missing from the result set")
            return {"message": "`party_name` column is missing from the result set", "status_code": 500}

        if doc_id_df.empty:
            logger.error("No records found matching the party name")
            return {"message": "No records found matching the party name", "status_code": 404}

        document_ids = doc_id_df["documentid"].tolist()

        placeholders = ", ".join(["?"] * len(document_ids))

        transactions_df = db.execute_df(f"SELECT * FROM aggregated_acris_records WHERE documentid IN ({placeholders}) ORDER BY documentid", document_ids)

        if transactions_df.empty:
            logger.error("No records found for the given party name")
            return {"message": "No records found for the given party name", "status_code": 404}

        return {
            "records": transactions_df.fillna(value="").to_dict(orient="records"),
            "status_code": 200,
        }

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return {"message": "An unexpected error has occurred", "status_code": 500}
