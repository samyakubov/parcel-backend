from database_connector import db
from logger_config import logger
import pandas as pd


def get_last_sold(bbl: str):
    if not _is_valid_bbl(bbl):
        error_msg = "Invalid BBL provided. It must be a non-empty string."
        logger.error(error_msg)
        return None

    try:
        sale_data = _get_latest_sale_record(bbl)
        deed_data = _get_latest_deed_record(bbl)

        sale_date = sale_data.get('sale_date') if sale_data else None
        deed_date = deed_data.get('sale_date') if deed_data else None

        if sale_date and deed_date and deed_date > sale_date:
            deed_data['year_built'] = sale_data['year_built']
            deed_data['land_sqft'] = sale_data['land_sqft']
            deed_data['gross_sqft'] = sale_data['gross_sqft']
            return deed_data

        if sale_data:
            if sale_data['last_sold_price']>0:
                return sale_data
            if deed_data:
                deed_data['year_built'] = sale_data['year_built']
                deed_data['land_sqft'] = sale_data['land_sqft']
                deed_data['gross_sqft'] = sale_data['gross_sqft']

        return deed_data

    except Exception as e:
        logger.error(f"Error in get_last_sold for BBL {bbl}: {e}")
        return None


def _is_valid_bbl(bbl: str) -> bool:
    return isinstance(bbl, str) and bbl.strip() != ""


def _get_latest_sale_record(bbl: str):
    sales_df = db.execute_df("SELECT * FROM aggregated_dof_sales WHERE bbl = ?", [bbl])
    if sales_df.empty:
        return None

    latest = sales_df.iloc[-1]
    try:
        sale_price = int(latest.sale_price)
        return {
            "last_sold_price": sale_price,
            "sale_date": latest.sale_date,
            "year_built": str(latest.year_built),
            "land_sqft": str(latest.land_square_feet),
            "gross_sqft": str(latest.gross_square_feet)
        }
    except (ValueError, AttributeError):
        logger.warning(f"Invalid data in annualized_sales for BBL: {bbl}")

    return None



def _get_latest_deed_record(bbl: str):
    deeds_df = _query_deed_records(bbl)
    if deeds_df.empty:
        return None

    latest = deeds_df.iloc[0]

    if latest.last_sold_price < 1000:
        return _handle_low_price_deed_case(bbl, deeds_df, latest)

    return {
        "last_sold_price": int(latest.last_sold_price),
        "sale_date": latest.sale_date
    }


def _query_deed_records(bbl: str) -> pd.DataFrame:
    query = """
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
            """
    return db.execute_df(query, [bbl])



def _handle_low_price_deed_case(bbl: str, deeds_df: pd.DataFrame, latest: pd.Series) :
    if len(deeds_df) > 1:
        prev = deeds_df.iloc[1]
        if prev.deed_party_name == latest.deed_party_name and prev.last_sold_price > 1000:
            return {
                "last_sold_price": int(prev.last_sold_price),
                "sale_date": prev.sale_date
            }

    return _match_deed_with_mortgage(bbl, deeds_df)


def _match_deed_with_mortgage(bbl: str, deeds_df: pd.DataFrame):
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
        return None

    mortgage_date = mortgage_df.iloc[0]["latest_mortgage_date"]
    matched = deeds_df[deeds_df["sale_date"] == mortgage_date]

    if matched.empty:
        return None

    deed = matched.iloc[0]
    return {
        "last_sold_price": int(deed.last_sold_price),
        "sale_date": deed.sale_date
    }
