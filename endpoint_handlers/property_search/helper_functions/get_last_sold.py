from typing import Optional
from database_connector import db
from endpoint_handlers.property_search.exceptions import InvalidBBLException
from logger_config import logger
import pandas as pd

from pydantic_models import LastSold


def get_last_sold(bbl: str) -> Optional[LastSold]:
    """Gets the last sold information for a given BBL.

    This function compares the latest sale record and the latest deed record to determine the most accurate
    last sold information.

    Args:
        bbl: The BBL (Borough-Block-Lot) of the property to get the last sold information for.

    Returns:
        A LastSold object containing the last sold information, or None if no information is found.

    Raises:
        InvalidBBLException: If the BBL is invalid.
    """
    if not isinstance(bbl, str) or not bbl.strip():
        raise InvalidBBLException
    try:
        logger.info(f"--------------------Fetching last sold information for BBL: {bbl}--------------------")
        sale_data = _get_latest_sale_record(bbl)
        deed_data = _get_latest_deed_record(bbl)
        sale_date = sale_data.last_sold_date if sale_data else None
        deed_date = deed_data.last_sold_date if deed_data else None

        logger.info(f"Latest sale record date: {sale_date}, Latest deed record date: {deed_date} for BBL: {bbl}")

        if sale_date and deed_date and deed_date > sale_date:
            logger.info(f"--------------------Deed date is more recent. Using deed data and augmenting with sale data for BBL: {bbl}--------------------\n")
            return LastSold(
                last_sold_price=deed_data.last_sold_price,
                last_sold_date=deed_date,
                year_built=sale_data.year_built,
                land_sqft=sale_data.land_sqft,
                gross_sqft=sale_data.gross_sqft
            )

        if sale_data:
            if sale_data.last_sold_price > 0:
                logger.info(f"--------------------Using latest sale record data for BBL: {bbl}--------------------\n")
                return LastSold(
                    last_sold_price=sale_data.last_sold_price,
                    last_sold_date=sale_date,
                    year_built=sale_data.year_built,
                    land_sqft=sale_data.land_sqft,
                    gross_sqft=sale_data.gross_sqft
                )
            if deed_data:
                logger.info(f"Sale price is zero. Appending property information from sale data: {bbl}")
                logger.info(f"--------------------Using latest deed record data for BBL: {bbl}--------------------\n")
                return LastSold(
                    last_sold_price=deed_data.last_sold_price,
                    last_sold_date=deed_date,
                    year_built=sale_data.year_built,
                    land_sqft=sale_data.land_sqft,
                    gross_sqft=sale_data.gross_sqft
                )
        logger.info(f"--------------------No definitive last sold data found, returning deed data for BBL: {bbl}--------------------\n")
        return LastSold(
            last_sold_price=deed_data.last_sold_price,
            last_sold_date=deed_date
        ) if deed_data else None
    except InvalidBBLException:
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_last_sold for BBL {bbl}: {e}", exc_info=True)
        return None


def _get_latest_sale_record(bbl: str) -> Optional[LastSold]:
    """Gets the latest sale record for a given BBL.

    Args:
        bbl: The BBL of the property.

    Returns:
        A LastSold object containing the latest sale record information, or None if no record is found.
    """
    logger.info(f"Querying for latest sale record for BBL: {bbl}")
    sales_df = db.execute_df("SELECT * FROM aggregated_dof_sales WHERE bbl = ?", [bbl])
    if sales_df.empty:
        logger.info(f"No DOF sales records found for BBL: {bbl}")
        return None

    latest = sales_df.iloc[-1]
    try:
        sale_price = int(latest.sale_price)
        logger.info(f"Found latest sale record for BBL {bbl} with price ${sale_price}")
        return LastSold(
            last_sold_price=sale_price,
            last_sold_date=latest.sale_date,
            year_built=latest.year_built,
            land_sqft=latest.land_square_feet,
            gross_sqft=latest.gross_square_feet
        )
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid data encountered in annualized_sales for BBL {bbl}: {e}", exc_info=True)
    return None


def _get_latest_deed_record(bbl: str) -> Optional[LastSold]:
    """Gets the latest deed record for a given BBL.

    Args:
        bbl: The BBL of the property.

    Returns:
        A LastSold object containing the latest deed record information, or None if no record is found.
    """
    logger.info(f"Querying for latest deed record for BBL: {bbl}")
    deeds_df = db.execute_df("""
                             SELECT
                                 amount AS last_sold_price,
                                 record_filed AS sale_date,
                                 party_name AS deed_party_name
                             FROM aggregated_acris_records
                             WHERE bbl = ?
                               AND doc_type = 'DEED'
                               AND amount > 0
                               AND partytype_desc = 'GRANTEE/BUYER'
                             ORDER BY record_filed DESC
                             """, [bbl])
    if deeds_df.empty:
        logger.info(f"No deed records found for BBL: {bbl}")
        return None

    latest = deeds_df.iloc[0]
    logger.info(f"Found latest deed record for BBL {bbl} with price ${latest.last_sold_price}")


    if latest.last_sold_price < 1000:
        logger.info(f"Deed price is low (< $1000). Attempting to find a more representative price for BBL: {bbl}")
        return _handle_low_price_deed_case(bbl, deeds_df, latest)

    return LastSold(
        last_sold_price=int(latest.last_sold_price),
        last_sold_date=latest.sale_date
    )


def _handle_low_price_deed_case(bbl: str, deeds_df: pd.DataFrame, latest: pd.Series) -> Optional[LastSold]:
    """Handles cases where the latest deed has a low price.

    This can happen in cases of deed transfers between family members or trusts.

    Args:
        bbl: The BBL of the property.
        deeds_df: A DataFrame of deed records.
        latest: The latest deed record.

    Returns:
        A LastSold object containing the last sold information, or the result of _match_deed_with_mortgage.
    """
    if len(deeds_df) > 1:
        prev = deeds_df.iloc[1]
        if prev.deed_party_name == latest.deed_party_name and prev.last_sold_price > 1000:
            logger.info(f"Found a previous deed with the same party name and higher price for BBL {bbl}. Using that price.")
            return LastSold(
                last_sold_price=int(prev.last_sold_price),
                last_sold_date=prev.sale_date
            )

    return _match_deed_with_mortgage(bbl, deeds_df)


def _match_deed_with_mortgage(bbl: str, deeds_df: pd.DataFrame) -> Optional[LastSold]:
    """Matches a low-price deed with a mortgage.

    Args:
        bbl: The BBL of the property.
        deeds_df: A DataFrame of deed records.

    Returns:
        A LastSold object containing the last sold information, or None if no match is found.
    """
    logger.info(f"Attempting to match low-price deed with a mortgage for BBL: {bbl}")
    query = """
            SELECT party_name AS mortgage_party_name, MAX(record_filed) AS latest_mortgage_date
            FROM aggregated_acris_records
            WHERE bbl = ?
              AND partytype_desc = 'MORTGAGOR/BORROWER'
              AND doc_type = 'MORTGAGE'
            GROUP BY party_name
            ORDER BY latest_mortgage_date DESC
                LIMIT 1
            """
    mortgage_df = db.execute_df(query, [bbl])
    if mortgage_df.empty:
        logger.info(f"No mortgage record found to match with deed for BBL: {bbl}")
        return None

    mortgage_date = mortgage_df.iloc[0]["latest_mortgage_date"]
    matched = deeds_df[deeds_df["sale_date"] == mortgage_date]

    if matched.empty:
        logger.info(f"Could not find a deed with the same date as the latest mortgage for BBL: {bbl}")
        return None

    deed = matched.iloc[0]
    logger.info(f"Found a matching deed and mortgage. Using deed price of ${deed.last_sold_price} for BBL: {bbl}")
    return LastSold(
        last_sold_price=int(deed.last_sold_price),
        last_sold_date=deed.sale_date
    )