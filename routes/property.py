from fastapi import APIRouter, Depends

from database_connector import DatabaseConnector, get_db
from handlers.api_keys.validate_api_key import validate_api_key
from handlers.property_search.search_by_property_address import (
    search_by_property_address,
)
from handlers.property_search.search_by_property_bbl import (
    search_by_property_bbl,
)
from schemas import PropertyDetailsResponse
from services.geolocation.coord_to_address import coord_to_address

property_routes = APIRouter(prefix="/property")


@property_routes.get(
    "/search_by_property_address/address={address}",
    dependencies=[Depends(validate_api_key)],
    response_model=PropertyDetailsResponse,
)
def search_by_address(
    address: str, record_filter: str | None = None, db: DatabaseConnector = Depends(get_db)
) -> PropertyDetailsResponse:
    """Searches for a property by its address.

    Args:
        address (str): The address of the property to search for.
        record_filter (str | None): Optional comma-separated list of doc_type values
            (e.g. "DEED,MORTGAGE") to restrict the returned `records` field to.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        PropertyDetailsResponse: A response object containing the property information.
    """
    filter_list = [v.strip() for v in record_filter.split(",") if v.strip()] if record_filter else None
    return search_by_property_address(address, db, filter_list)


@property_routes.get(
    "/search_by_property_bbl/bbl={bbl}",
    dependencies=[Depends(validate_api_key)],
    response_model=PropertyDetailsResponse,
)
def search_by_bbl(
    bbl: str, record_filter: str | None = None, db: DatabaseConnector = Depends(get_db)
) -> PropertyDetailsResponse:
    """Searches for a property by its BBL (Borough, Block, Lot).

    Args:
        bbl (str): The BBL of the property to search for.
        record_filter (str | None): Optional comma-separated list of doc_type values
            (e.g. "DEED,MORTGAGE") to restrict the returned `records` field to.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        PropertyDetailsResponse: A response object containing the property information.
    """
    filter_list = [v.strip() for v in record_filter.split(",") if v.strip()] if record_filter else None
    return search_by_property_bbl(bbl, db, filter_list)


@property_routes.get(
    "/search_by_fuzzy_coords/lat={lat}/long={long}",
    dependencies=[Depends(validate_api_key)],
    response_model=PropertyDetailsResponse,
)
def search_by_fuzz_coords(
    lat: str, long: str, db: DatabaseConnector = Depends(get_db)
) -> PropertyDetailsResponse:
    """Searches for a property by its fuzzy coordinates.

    Args:
        lat (str): The latitude of the property.
        long (str): The longitude of the property.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        PropertyDetailsResponse: A response object containing the property information.
    """
    address = coord_to_address(float(lat), float(long))["address"]
    return search_by_property_address(address, db)
