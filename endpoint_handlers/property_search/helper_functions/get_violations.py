from database_connector import db
from logger_config import logger


def get_violations(bbl:str):
    try:
        violations_df = db.execute_df("""SELECT bbl, 
                                                violation_status, 
                                                issue_date, 
                                                violation_type, 
                                                description, 
                                                severity, 
                                                penalty_amount, 
                                                amount_paid, 
                                                balance_due, 
                                                respondent_name, 
                                                house_number, 
                                                street, 
                                                city, 
                                                zip 
                                         FROM aggregated_acris_violations WHERE bbl = ?
                                      """, [bbl])
        if violations_df.empty:
            return []

        return violations_df.fillna("").to_dict(orient="records")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []
