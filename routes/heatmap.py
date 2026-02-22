from datetime import date

from fastapi import APIRouter, Depends, Query

from database_connector import DatabaseConnector, get_db
from handlers.api_keys.validate_api_key import validate_api_key
from handlers.heatmap.get_zipcode_heatmap import get_zipcode_heatmap
from schemas import HeatmapResponse

heatmap_routes = APIRouter(prefix="/heatmap")
@heatmap_routes.get(
    "/zipcode",
    dependencies=[Depends(validate_api_key)],
    response_model=HeatmapResponse,
)
def get_zipcode_heatmap_route(
    start_date: str | None = Query(f"{date.today().year-1}-01-01", description="Start date (YYYY-MM-DD)"),
    end_date: str | None = Query(f"{date.today().year-1}-12-31", description="End date (YYYY-MM-DD)"),
    db: DatabaseConnector = Depends(get_db),
) -> HeatmapResponse:
    """Gets aggregated property sales data by ZIP code for a heatmap.

    Args:
        start_date (str | None): Optional start date filter in YYYY-MM-DD format.
        end_date (str | None): Optional end date filter in YYYY-MM-DD format.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        HeatmapResponse: Aggregated sales data.
    """
    return get_zipcode_heatmap(db, start_date, end_date)
