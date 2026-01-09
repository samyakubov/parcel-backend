from fastapi import APIRouter

from services.census.geocode_address import geocode_address
from services.census.get_census_data import get_census_data_handler

census_routes = APIRouter(prefix="/census")


@census_routes.get("/get_census_data/address={address}")
def get_census_data(address: str):
    """
    Gets census data for a given address.

    Args:
        address: The address to get census data for.

    Returns:
        A dictionary containing census data.
    """
    geo_data = geocode_address(address)

    return get_census_data_handler(geo_data["tract"])
