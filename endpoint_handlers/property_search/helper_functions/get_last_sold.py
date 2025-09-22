from database_connector import db
from logger_config import logger
import pandas as pd

LOW_PRICE_THRESHOLD = 1000

def get_last_sold(bbl: str):
    if not bbl or not isinstance(bbl, str):
        error_msg = "Invalid BBL provided. It must be a non-empty string."
        logger.error(error_msg)
        return error_msg

    try:
        deeds_df = _get_deed_records(bbl)
        if deeds_df.empty:
            logger.warning(f"No deed records found for BBL: {bbl}")
            return []

        latest_deed = deeds_df.iloc[0]

        if latest_deed.last_sold_price < LOW_PRICE_THRESHOLD:
            if len(deeds_df) > 1:
                prev_deed = deeds_df.iloc[1]
                if prev_deed.deed_party_name == latest_deed.deed_party_name:
                    return {
                        "last_sold_price": int(prev_deed.last_sold_price),
                        "sale_date": prev_deed.sale_date
                    }

            mortgage_result = _handle_low_price_case(bbl, deeds_df)
            if mortgage_result:
                return mortgage_result

            logger.warning(f"No matching deed with party name and price > 0 for BBL: {bbl}")
            return []

        return {
            "last_sold_price": int(latest_deed.last_sold_price),
            "sale_date": latest_deed.sale_date
        }

    except Exception as e:
        logger.error(f"Error in get_last_sold for BBL {bbl}: {e}")
        return []


def _get_deed_records(bbl: str):
    query = """
            SELECT
                amount AS last_sold_price,
                recordedfiled AS sale_date,
                party_name AS deed_party_name
            FROM AcrisPropertyAggregate
            WHERE bbl = ?
              AND doc_type = 'DEED'
              AND amount > 0
              AND partytype_desc = 'GRANTEE/BUYER'
            ORDER BY recordedfiled DESC
                LIMIT 10 \
            """
    return db.execute_df(query, [bbl])


def _handle_low_price_case(bbl: str, deeds_df: pd.DataFrame):
    # Get latest mortgage per party
    mortgage_subquery = """
                        SELECT party_name AS mortgage_party_name, MAX(recordedfiled) AS latest_mortgage_date
                        FROM AcrisPropertyAggregate
                        WHERE bbl = ?
                          AND partytype_desc = 'MORTGAGOR/BORROWER'
                          AND doc_type = 'MORTGAGE'
                        GROUP BY party_name
                        ORDER BY latest_mortgage_date DESC
                            LIMIT 1 \
                        """
    latest_mortgage = db.execute_df(mortgage_subquery, [bbl])
    if latest_mortgage.empty:
        logger.warning(f"No mortgage record found for BBL: {bbl}")
        return None

    mortgage_date = latest_mortgage.iloc[0]["latest_mortgage_date"]
    matching_deeds = deeds_df[deeds_df["sale_date"] == mortgage_date]

    if matching_deeds.empty:
        return None

    latest_sale = matching_deeds.iloc[0]
    return {
        "last_sold_price": int(latest_sale.last_sold_price),
        "sale_date": latest_sale.sale_date
    }
