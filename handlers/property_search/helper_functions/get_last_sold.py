import pandas as pd

from exceptions.property_search_exceptions import InvalidBBLError
from logger_config import logger
from schemas import LastSold


def get_last_sold(bbl: str, sales_df: pd.DataFrame, acris_df: pd.DataFrame) -> LastSold | None:
    if not isinstance(bbl, str) or not bbl.strip():
        raise InvalidBBLError
    try:
        logger.info(f"Processing last sold for BBL: {bbl}")

        sale = _get_dof_sale(sales_df)
        deed = _get_best_deed_price(acris_df)
        pluto = _get_pluto_stats(acris_df)

        sale_price = sale["price"] if sale else None
        sale_date = sale["date"] if sale else None
        deed_price, deed_date = deed if deed else (None, None)

        # Pick price and date: deed wins if more recent or sale price is zero
        if deed_date and sale_date:
            if deed_date > sale_date or not sale_price:
                price, date = deed_price, deed_date
            else:
                price, date = sale_price, sale_date
        elif sale_date:
            price, date = sale_price, sale_date
        elif deed_date:
            price, date = deed_price, deed_date
        else:
            return None

        # Stats: DOF sales first, PLUTO as fallback
        year_built = (sale.get("year_built") if sale else None) or pluto.get("year_built")
        land_sqft = (sale.get("land_sqft") if sale else None) or pluto.get("land_sqft")
        gross_sqft = (sale.get("gross_sqft") if sale else None) or pluto.get("gross_sqft")

        return LastSold(
            last_sold_price=price,
            last_sold_date=date,
            year_built=year_built,
            land_sqft=land_sqft,
            gross_sqft=gross_sqft,
        )
    except InvalidBBLError:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in get_last_sold for BBL {bbl}: {e}", exc_info=True)
        return None


def _get_dof_sale(sales_df: pd.DataFrame) -> dict | None:
    if sales_df.empty:
        return None
    latest = sales_df.iloc[-1]
    try:
        return {
            "price": int(latest.sale_price),
            "date": latest.sale_date,
            "year_built": _safe_int(latest.year_built),
            "land_sqft": _safe_int(latest.land_square_feet),
            "gross_sqft": _safe_int(latest.gross_square_feet),
        }
    except (ValueError, AttributeError) as e:
        logger.error(f"Invalid data in DOF sales record: {e}", exc_info=True)
        return None


def _get_best_deed_price(acris_df: pd.DataFrame) -> tuple[int, object] | None:
    if acris_df.empty:
        return None

    mask = (
        (acris_df["doc_type"] == "DEED") &
        (acris_df["amount"] > 0) &
        (acris_df["partytype_desc"] == "GRANTEE/BUYER")
    )
    deeds = acris_df[mask].sort_values("record_filed", ascending=False)

    if deeds.empty:
        return None

    latest = deeds.iloc[0]
    price = int(latest["amount"])

    if price >= 1000:
        return price, latest["record_filed"]

    # Low price: try same buyer's previous deed with a real price
    if len(deeds) > 1:
        rest = deeds.iloc[1:]
        higher = rest[(rest["party_name"] == latest["party_name"]) & (rest["amount"] > 1000)]
        if not higher.empty:
            row = higher.iloc[0]
            return int(row["amount"]), row["record_filed"]

    # Fall back to matching with a same-date mortgage
    return _price_from_mortgage(deeds, acris_df)


def _price_from_mortgage(deeds: pd.DataFrame, acris_df: pd.DataFrame) -> tuple[int, object] | None:
    mortgages = acris_df[
        (acris_df["doc_type"] == "MORTGAGE") &
        (acris_df["partytype_desc"] == "MORTGAGOR/BORROWER")
    ]
    if mortgages.empty:
        return None

    latest_mortgage_date = mortgages.groupby("party_name")["record_filed"].max().max()
    matched = deeds[deeds["record_filed"] == latest_mortgage_date]

    if matched.empty:
        return None

    row = matched.iloc[0]
    return int(row["amount"]), row["record_filed"]


def _get_pluto_stats(acris_df: pd.DataFrame) -> dict:
    if acris_df.empty:
        return {}
    row = acris_df.iloc[0]
    return {
        "year_built": _safe_int(row.get("year_built")),
        "land_sqft": _safe_int(row.get("lot_area")),
        "gross_sqft": _safe_int(row.get("bldg_area")),
    }


def _safe_int(v) -> int | None:
    try:
        return None if pd.isna(v) else int(v)
    except (TypeError, ValueError):
        return None
