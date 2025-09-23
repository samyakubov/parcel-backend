from database_connector import db
from logger_config import logger


def get_violation_data(bbl:str):
    try:
        violations_df = db.execute_df("""SELECT bbl, 
                                                violation_status, 
                                                issuedate as issue_date, 
                                                violationtype as violation_type, 
                                                description, 
                                                severity, 
                                                penalty_amount, 
                                                amountpaid as amount_paid, 
                                                balancedue as balance_due, 
                                                respondentname as respondent_name, 
                                                house_number, 
                                                street, 
                                                city, zip 
                                         FROM aggregated_acris_violations WHERE bbl = ?""", [bbl])
        if violations_df.empty:
            return []

        return violations_df.fillna("").to_dict(orient="records")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
