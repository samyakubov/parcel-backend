from database_connector import db
from logger_config import logger


def get_violation_data(bbl:str):
    try:
        violations_df = db.execute_df("SELECT bbl, violation_status, issuedate, violationtype, description, severity, penalty_amount, amountpaid, balancedue, respondentname, house_number, street, city, zip FROM aggregated_acris_violations WHERE bbl = ?", [bbl])
        if violations_df.empty:
            return []

        return violations_df.fillna("").to_dict(orient="records")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
