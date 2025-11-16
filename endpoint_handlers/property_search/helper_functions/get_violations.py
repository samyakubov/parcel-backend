from typing import List
from database_connector import DatabaseConnector
from logger_config import logger
from pydantic_models import Violation


def get_violations(bbl: str, db: DatabaseConnector) -> List[Violation]:
    """Gets violations for a given BBL.

    Args:
        bbl: The BBL (Borough-Block-Lot) of the property to get violations for.
        db: The database connector instance.

    Returns:
        A list of Violation objects containing violation information.
        Returns an empty list if no violations are found or if an error occurs.
    """
    if not bbl:
        logger.warning("Attempted to get violations without a BBL.")
        return []
    try:
        logger.info(f"--------------------Fetching violations for BBL: {bbl}--------------------")
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
            logger.info(f"--------------------No violations found for BBL: {bbl}--------------------\n")
            return []

        logger.info(f"--------------------Found {len(violations_df)} violations for BBL: {bbl}--------------------\n")
        return violations_df.fillna("").to_dict(orient="records")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching violations for BBL {bbl}: {e}", exc_info=True)
        return []