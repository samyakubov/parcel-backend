import pandas as pd

from database_connector import DatabaseConnector
from logger_config import logger
from schemas import HeatmapResponse, ZipCodeHeatmapItem


def get_zipcode_heatmap(
    db: DatabaseConnector, start_date: str | None = None, end_date: str | None = None
) -> HeatmapResponse:
    """
    Aggregates property sales data by ZIP code.

    Args:
        db (DatabaseConnector): The database connector instance.
        start_date (str | None): Optional start date filter (YYYY-MM-DD).
        end_date (str | None): Optional end date filter (YYYY-MM-DD).

    Returns:
        HeatmapResponse: Aggregated sales data by ZIP code.
    """
    logger.info(f"Generating ZIP code heatmap. Start: {start_date}, End: {end_date}")

    params = []
    where_clauses = ["sale_price IS NOT NULL", "CAST(REGEXP_REPLACE(sale_price, '[^0-9.]', '', 'g') AS BIGINT) > 0", "length(trim(zip_code)) = 5"]

    if start_date:
        where_clauses.append("sale_date >= ?")
        params.append(start_date)
    if end_date:
        where_clauses.append("sale_date <= ?")
        params.append(end_date)

    where_str = " AND ".join(where_clauses)

    query = f"""
    SELECT
        zip_code,
        COUNT(*) as num_sales,
        MEDIAN(CAST(REGEXP_REPLACE(sale_price, '[^0-9.]', '', 'g') AS BIGINT)) as median_price,
        AVG(CAST(REGEXP_REPLACE(sale_price, '[^0-9.]', '', 'g') AS BIGINT)) as avg_price,
        MEDIAN(
            CASE 
                WHEN gross_square_feet > 0 
                THEN CAST(REGEXP_REPLACE(sale_price, '[^0-9.]', '', 'g') AS BIGINT) / gross_square_feet 
                ELSE NULL 
            END
        ) as median_price_per_sqft
    FROM aggregated_dof_sales
    WHERE {where_str}
    GROUP BY zip_code
    ORDER BY num_sales DESC
    """

    try:
        df = db.execute_df(query, params)
        
        heatmap_items = []
        for _, row in df.iterrows():
            item = ZipCodeHeatmapItem(
                zip_code=str(row["zip_code"]),
                num_sales=int(row["num_sales"]),
                median_price=float(row["median_price"]) if not pd.isna(row["median_price"]) else 0.0,
                avg_price=float(row["avg_price"]) if not pd.isna(row["avg_price"]) else 0.0,
                median_price_per_sqft=float(row["median_price_per_sqft"]) if not pd.isna(row["median_price_per_sqft"]) else None,
            )
            heatmap_items.append(item)

        return HeatmapResponse(
            data=heatmap_items,
            start_date=start_date,
            end_date=end_date,
        )

    except Exception as e:
        logger.error(f"Failed to generate ZIP code heatmap: {e}", exc_info=True)
        raise
