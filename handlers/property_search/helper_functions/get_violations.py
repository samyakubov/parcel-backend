import pandas as pd
from logger_config import logger
from schemas import Violation


def get_violations(bbl: str, violations_df: pd.DataFrame) -> list[Violation]:
    """Gets violations for a given BBL.

    Args:
        bbl: The BBL (Borough-Block-Lot) of the property to get violations for.
        violations_df: DataFrame containing violations data.

    Returns:
        A list of Violation objects containing violation information.
        Returns an empty list if no violations are found or if an error occurs.
    """
    if not bbl:
        logger.warning("Attempted to get violations without a BBL.")
        return []
    
    if violations_df.empty:
        logger.info(f"--------------------No violations found for BBL: {bbl}--------------------\n")
        return []

    try:
        logger.info(f"--------------------Processing violations for BBL: {bbl}--------------------")
        
        # Raw columns in standard schema:
        # bbl, violation_status, issue_date, violation_type, description, severity, 
        # penalty_amount, amount_paid, balance_due, respondent_name, house_number, street, city, zip
        
        # We need to ensure the DF allows us to map to Schema.
        # Assuming the DF passed is simply the relevant rows from `aggregated_acris_violations`
        
        # Just return dict records if the columns match.
        # If columns need renaming, we might need a map. 
        # The original SQL selected specific columns. 
        
        # Assuming table columns match schema field names or are close enough that we just dump them?
        # The original SQL was: `SELECT bbl, violation_status, ...`
        
        logger.info(f"--------------------Found {len(violations_df)} violations for BBL: {bbl}--------------------\n")
        return violations_df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"An unexpected error occurred while fetching violations for BBL {bbl}: {e}", exc_info=True)
        return []
