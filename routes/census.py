from fastapi import APIRouter, Depends, HTTPException

from database_connector import DatabaseConnector, get_db
from services.census.geocode_address import geocode_address
from services.census.get_census_data import get_census_data_handler

census_routes = APIRouter(prefix="/census")


@census_routes.get("/get_census_data/address={address}")
def get_census_data(address: str):
    """
    Gets census data for a given address.

    Args:
        address (str): The address to get census data for.

    Returns:
        dict: A dictionary containing census data.

    Raises:
        HTTPException: If the address cannot be geocoded.
    """
    try:
        geo_data = geocode_address(address)
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

    return get_census_data_handler(geo_data["tract"])


@census_routes.get("/get_census_data/bbl={bbl}")
def get_census_data_by_bbl(bbl: str, db: DatabaseConnector = Depends(get_db)):
    """
    Gets census data for a given BBL.

    Args:
        bbl (str): The BBL to get census data for.
        db (DatabaseConnector): The database connector.

    Returns:
        dict: A dictionary containing census data.

    Raises:
        HTTPException: If the BBL is not found or address cannot be geocoded.
    """
    query = """
    SELECT prop_streetnumber, prop_streetname
    FROM aggregated_acris_records
    WHERE bbl = ?
    LIMIT 1
    """
    df = db.execute_df(query, [bbl])

    if df.empty:
        raise HTTPException(status_code=404, detail=f"No address found for BBL {bbl}")

    street_number = df.iloc[0]['prop_streetnumber']
    street_name = df.iloc[0]['prop_streetname']

    if not street_number or not street_name:
        raise HTTPException(status_code=404, detail=f"Incomplete address records for BBL {bbl}")

    address = f"{street_number} {street_name}"

    try:
        geo_data = geocode_address(address)
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Could not geocode address '{address}' for BBL {bbl}: {str(e)}")

    return get_census_data_handler(geo_data["tract"])
