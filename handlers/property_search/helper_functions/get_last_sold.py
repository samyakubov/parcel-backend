import pandas as pd

from exceptions.property_search_exceptions import InvalidBBLError
from logger_config import logger
from schemas import LastSold


def get_last_sold(bbl: str, sales_df: pd.DataFrame, acris_df: pd.DataFrame) -> LastSold | None:
    """Gets the last sold information for a given BBL.

    This function compares the latest sale record and the latest deed record to determine the most accurate
    last sold information.

    Args:
        bbl: The BBL (Borough-Block-Lot) of the property to get the last sold information for.
        sales_df: DataFrame containing DOF sales data.
        acris_df: DataFrame containing ACRIS records.

    Returns:
        A LastSold object containing the last sold information, or None if no information is found.

    Raises:
        InvalidBBLError: If the BBL is invalid.
    """
    if not isinstance(bbl, str) or not bbl.strip():
        raise InvalidBBLError
    try:
        logger.info(f"--------------------Analyzing last sold information for BBL: {bbl}--------------------")

        sale_data = _get_latest_sale_record(bbl, sales_df)
        deed_data = _get_latest_deed_record(bbl, acris_df)

        sale_date = sale_data.last_sold_date if sale_data else None
        deed_date = deed_data.last_sold_date if deed_data else None

        logger.info(f"Latest sale record date: {sale_date}, Latest deed record date: {deed_date} for BBL: {bbl}")

        if sale_date and deed_date and deed_date > sale_date:
            logger.info(
                f"--------------------Deed date is more recent. Using deed data and augmenting with sale data for BBL: {bbl}--------------------\n"
            )
            return LastSold(
                last_sold_price=deed_data.last_sold_price,
                last_sold_date=deed_date,
                year_built=sale_data.year_built,
                land_sqft=sale_data.land_sqft,
                gross_sqft=sale_data.gross_sqft,
            )

        if sale_data:
            if sale_data.last_sold_price > 0:
                logger.info(f"--------------------Using latest sale record data for BBL: {bbl}--------------------\n")
                return LastSold(
                    last_sold_price=sale_data.last_sold_price,
                    last_sold_date=sale_date,
                    year_built=sale_data.year_built,
                    land_sqft=sale_data.land_sqft,
                    gross_sqft=sale_data.gross_sqft,
                )
            if deed_data:
                logger.info(f"Sale price is zero. Appending property information from sale data: {bbl}")
                logger.info(f"--------------------Using latest deed record data for BBL: {bbl}--------------------\n")
                return LastSold(
                    last_sold_price=deed_data.last_sold_price,
                    last_sold_date=deed_date,
                    year_built=sale_data.year_built,
                    land_sqft=sale_data.land_sqft,
                    gross_sqft=sale_data.gross_sqft,
                )
        logger.info(
            f"--------------------No definitive last sold data found, returning deed data for BBL: {bbl}--------------------\n"
        )
        return LastSold(last_sold_price=deed_data.last_sold_price, last_sold_date=deed_date) if deed_data else None
    except InvalidBBLError:
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_last_sold for BBL {bbl}: {e}", exc_info=True)
        return None


def _get_latest_sale_record(bbl: str, sales_df: pd.DataFrame) -> LastSold | None:
    """Gets the latest sale record for a given BBL."""
    logger.info(f"Scanning latest sale record for BBL: {bbl}")

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
            gross_sqft=latest.gross_square_feet,
        )
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid data encountered in annualized_sales for BBL {bbl}: {e}", exc_info=True)
    return None


def _get_latest_deed_record(bbl: str, acris_df: pd.DataFrame) -> LastSold | None:
    """Gets the latest deed record for a given BBL."""
    logger.info(f"Scanning latest deed record for BBL: {bbl}")

    if acris_df.empty:
        logger.info(f"No acris records found for BBL: {bbl}")
        return None

    mask = (
        (acris_df["doc_type"] == 'DEED') &
        (acris_df["amount"] > 0) &
        (acris_df["partytype_desc"] == 'GRANTEE/BUYER')
    )
    deeds_df = acris_df[mask].sort_values(by="record_filed", ascending=False)

    if deeds_df.empty:
        logger.info(f"No deed records found for BBL: {bbl}")
        return None

    latest = deeds_df.iloc[0]

    last_sold_price = latest["amount"]

    logger.info(f"Found latest deed record for BBL {bbl} with price ${last_sold_price}")

    if last_sold_price < 1000:
        logger.info(f"Deed price is low (< $1000). Attempting to find a more representative price for BBL: {bbl}")
        return _handle_low_price_deed_case(bbl, deeds_df, latest, acris_df)

    return LastSold(last_sold_price=int(last_sold_price), last_sold_date=latest["record_filed"])


def _handle_low_price_deed_case(
    bbl: str, deeds_df: pd.DataFrame, latest: pd.Series, acris_df: pd.DataFrame
) -> LastSold | None:
    """Handles cases where the latest deed has a low price."""
    if len(deeds_df) > 1:
        prev = deeds_df.iloc[1]
        if prev["party_name"] == latest["party_name"] and prev["amount"] > 1000:
             logger.info(
                f"Found a previous deed with the same party name and higher price for BBL {bbl}. Using that price."
            )
             return LastSold(last_sold_price=int(prev["amount"]), last_sold_date=prev["record_filed"])

    return _match_deed_with_mortgage(bbl, deeds_df, acris_df)


def _match_deed_with_mortgage(bbl: str, deeds_df: pd.DataFrame, acris_df: pd.DataFrame) -> LastSold | None:
    """Matches a low-price deed with a mortgage."""
    logger.info(f"Attempting to match low-price deed with a mortgage for BBL: {bbl}")

    mask = (
        (acris_df["doc_type"] == 'MORTGAGE') &
        (acris_df["partytype_desc"] == 'MORTGAGOR/BORROWER')
    )

    mortgages = acris_df[mask].copy()

    if mortgages.empty:
         logger.info(f"No mortgage record found to match with deed for BBL: {bbl}")
         return None

    latest_mortgages = mortgages.groupby("party_name")["record_filed"].max().reset_index()
    latest_mortgages = latest_mortgages.sort_values(by="record_filed", ascending=False)

    if latest_mortgages.empty:
        logger.info(f"No mortgage record found to match with deed for BBL: {bbl}")
        return None

    mortgage_date = latest_mortgages.iloc[0]["record_filed"]

    matched = deeds_df[deeds_df["record_filed"] == mortgage_date]

    if matched.empty:
        logger.info(f"Could not find a deed with the same date as the latest mortgage for BBL: {bbl}")
        return None

    deed = matched.iloc[0]
    logger.info(f"Found a matching deed and mortgage. Using deed price of ${deed['amount']} for BBL: {bbl}")
    return LastSold(last_sold_price=int(deed['amount']), last_sold_date=deed['record_filed'])
