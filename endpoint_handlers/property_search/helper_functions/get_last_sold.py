from database_connector import db
from endpoint_handlers.property_search.exceptions import InvalidBBLException
from logger_config import logger
import pandas as pd


def get_last_sold(bbl: str):
    if not isinstance(bbl, str) or not bbl.strip():
        error_msg = f"Invalid BBL provided in get_last_sold: '{bbl}'"
        logger.error(error_msg)
        raise InvalidBBLException(error_msg)
    try:
        logger.info(f"--------------------Fetching last sold information for BBL: {bbl}--------------------")
        sale_data = _get_latest_sale_record(bbl)
        deed_data = _get_latest_deed_record(bbl)

        sale_date = sale_data.get('sale_date') if sale_data else None
        deed_date = deed_data.get('sale_date') if deed_data else None

        logger.info(f"Latest sale record date: {sale_date}, Latest deed record date: {deed_date} for BBL: {bbl}")

        if sale_date and deed_date and deed_date > sale_date:
            logger.info(f"--------------------Deed date is more recent. Using deed data and augmenting with sale data for BBL: {bbl}--------------------\n")
            deed_data['year_built'] = sale_data.get('year_built')
            deed_data['land_sqft'] = sale_data.get('land_sqft')
            deed_data['gross_sqft'] = sale_data.get('gross_sqft')
            return deed_data

        if sale_data:
            if sale_data.get('last_sold_price', 0) > 0:
                logger.info(f"--------------------Using latest sale record data for BBL: {bbl}--------------------\n")
                return sale_data
            if deed_data:
                logger.info(f"Sale price is zero. Appending property information from sale data: {bbl}")
                deed_data['year_built'] = sale_data.get('year_built')
                deed_data['land_sqft'] = sale_data.get('land_sqft')
                deed_data['gross_sqft'] = sale_data.get('gross_sqft')
                logger.info(f"--------------------Using latest deed record data for BBL: {bbl}--------------------\n")
                return deed_data

        logger.info(f"--------------------No definitive last sold data found, returning deed data for BBL: {bbl}--------------------\n")
        return deed_data
    except InvalidBBLException:
        raise
    except Exception as e:
        logger.error(f"An unexpected error occurred in get_last_sold for BBL {bbl}: {e}", exc_info=True)
        return None


def _get_latest_sale_record(bbl: str):
    logger.info(f"Querying for latest sale record for BBL: {bbl}")
    sales_df = db.execute_df("SELECT * FROM aggregated_dof_sales WHERE bbl = ?", [bbl])
    if sales_df.empty:
        logger.info(f"No DOF sales records found for BBL: {bbl}")
        return None

    latest = sales_df.iloc[-1]
    try:
        sale_price = int(latest.sale_price)
        logger.info(f"Found latest sale record for BBL {bbl} with price ${sale_price}")
        return {
            "last_sold_price": sale_price,
            "sale_date": latest.sale_date,
            "year_built": str(latest.year_built),
            "land_sqft": str(latest.land_square_feet),
            "gross_sqft": str(latest.gross_square_feet)
        }
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid data encountered in annualized_sales for BBL {bbl}: {e}", exc_info=True)

    return None


def _get_latest_deed_record(bbl: str):
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

    return {
        "last_sold_price": int(latest.last_sold_price),
        "sale_date": latest.sale_date
    }

#this is to handle deed transfers between family members/trusts
def _handle_low_price_deed_case(bbl: str, deeds_df: pd.DataFrame, latest: pd.Series) :
    if len(deeds_df) > 1:
        prev = deeds_df.iloc[1]
        if prev.deed_party_name == latest.deed_party_name and prev.last_sold_price > 1000:
            logger.info(f"Found a previous deed with the same party name and higher price for BBL {bbl}. Using that price.")
            return {
                "last_sold_price": int(prev.last_sold_price),
                "sale_date": prev.sale_date
            }

    return _match_deed_with_mortgage(bbl, deeds_df)

#TODO:Find out why I did this
def _match_deed_with_mortgage(bbl: str, deeds_df: pd.DataFrame):
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
    return {
        "last_sold_price": int(deed.last_sold_price),
        "sale_date": deed.sale_date
    }