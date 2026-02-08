import pandas as pd

from database_connector import DatabaseConnector
from exceptions.property_search_exceptions import InvalidBBLError
from logger_config import logger
from schemas import LastSold


def get_last_sold(bbl: str, acris_df: pd.DataFrame, db: DatabaseConnector) -> LastSold | None:
    """Gets the last sold information for a given BBL.

    This function compares the latest sale record and the latest deed record to determine the most accurate
    last sold information.

    Args:
        bbl: The BBL (Borough-Block-Lot) of the property to get the last sold information for.
        acris_df: Pre-fetched ACRIS records for this BBL.
        db: The database connector instance (used only for DOF sales lookup).

    Returns:
        A LastSold object containing the last sold information, or None if no information is found.

    Raises:
        InvalidBBLError: If the BBL is invalid.
    """
    if not isinstance(bbl, str) or not bbl.strip():
        raise InvalidBBLError
    try:
        logger.info(f"--------------------Fetching last sold information for BBL: {bbl}--------------------")
        sale_data = _get_latest_sale_record(bbl, db)
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


def _get_latest_sale_record(bbl: str, db: DatabaseConnector) -> LastSold | None:
    """Gets the latest sale record for a given BBL.

    Args:
        bbl: The BBL of the property.
        db: The database connector instance.

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
            gross_sqft=latest.gross_square_feet,
        )
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid data encountered in annualized_sales for BBL {bbl}: {e}", exc_info=True)
    return None


def _get_latest_deed_record(bbl: str, acris_df: pd.DataFrame) -> LastSold | None:
    """Gets the latest deed record for a given BBL.

    Args:
        bbl: The BBL of the property.
        acris_df: Pre-fetched ACRIS records for this BBL.

    Returns:
        A LastSold object containing the latest deed record information, or None if no record is found.
    """
    logger.info(f"Querying for latest deed record for BBL: {bbl}")
    deeds_df = acris_df[
        (acris_df["doc_type"] == "DEED")
        & (acris_df["amount"] > 0)
        & (acris_df["partytype_desc"] == "GRANTEE/BUYER")
    ][["amount", "record_filed", "party_name"]].copy()

    deeds_df = deeds_df.rename(columns={
        "amount": "last_sold_price",
        "record_filed": "sale_date",
        "party_name": "deed_party_name",
    }).sort_values("sale_date", ascending=False).reset_index(drop=True)

    if deeds_df.empty:
        logger.info(f"No deed records found for BBL: {bbl}")
        return None

    latest = deeds_df.iloc[0]
    logger.info(f"Found latest deed record for BBL {bbl} with price ${latest.last_sold_price}")

    if latest.last_sold_price < 1000:
        logger.info(f"Deed price is low (< $1000). Attempting to find a more representative price for BBL: {bbl}")
        return _handle_low_price_deed_case(bbl, deeds_df, latest, acris_df)

    return LastSold(last_sold_price=int(latest.last_sold_price), last_sold_date=latest.sale_date)


def _handle_low_price_deed_case(
    bbl: str, deeds_df: pd.DataFrame, latest: pd.Series, acris_df: pd.DataFrame
) -> LastSold | None:
    """Handles cases where the latest deed has a low price.

    This can happen in cases of deed transfers between family members or trusts.

    Args:
        bbl: The BBL of the property.
        deeds_df: A DataFrame of deed records.
        latest: The latest deed record.
        acris_df: Pre-fetched ACRIS records for this BBL.

    Returns:
        A LastSold object containing the last sold information, or the result of _match_deed_with_mortgage.
    """
    if len(deeds_df) > 1:
        prev = deeds_df.iloc[1]
        if prev.deed_party_name == latest.deed_party_name and prev.last_sold_price > 1000:
            logger.info(
                f"Found a previous deed with the same party name and higher price for BBL {bbl}. Using that price."
            )
            return LastSold(last_sold_price=int(prev.last_sold_price), last_sold_date=prev.sale_date)

    return _match_deed_with_mortgage(bbl, deeds_df, acris_df)


def _match_deed_with_mortgage(bbl: str, deeds_df: pd.DataFrame, acris_df: pd.DataFrame) -> LastSold | None:
    """Matches a low-price deed with a mortgage.

    Args:
        bbl: The BBL of the property.
        deeds_df: A DataFrame of deed records.
        acris_df: Pre-fetched ACRIS records for this BBL.

    Returns:
        A LastSold object containing the last sold information, or None if no match is found.
    """
    logger.info(f"Attempting to match low-price deed with a mortgage for BBL: {bbl}")

    mortgage_borrowers = acris_df[
        (acris_df["partytype_desc"] == "MORTGAGOR/BORROWER")
        & (acris_df["doc_type"] == "MORTGAGE")
    ]

    if mortgage_borrowers.empty:
        logger.info(f"No mortgage record found to match with deed for BBL: {bbl}")
        return None

    grouped = mortgage_borrowers.groupby("party_name")["record_filed"].max().reset_index()
    grouped.columns = ["mortgage_party_name", "latest_mortgage_date"]
    grouped = grouped.sort_values("latest_mortgage_date", ascending=False)

    mortgage_date = grouped.iloc[0]["latest_mortgage_date"]
    matched = deeds_df[deeds_df["sale_date"] == mortgage_date]

    if matched.empty:
        logger.info(f"Could not find a deed with the same date as the latest mortgage for BBL: {bbl}")
        return None

    deed = matched.iloc[0]
    logger.info(f"Found a matching deed and mortgage. Using deed price of ${deed.last_sold_price} for BBL: {bbl}")
    return LastSold(last_sold_price=int(deed.last_sold_price), last_sold_date=deed.sale_date)
