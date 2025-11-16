from typing import Dict, Union
from fastapi import APIRouter, Depends
from database_connector import DatabaseConnector
from database_connector import get_db
from endpoint_handlers.api_keys.validate_api_key import validate_api_key
from endpoint_handlers.property_search.search_by_property_address import search_by_property_address
from endpoint_handlers.property_search.search_by_property_bbl import search_by_property_bbl
from pydantic_models import PropertyDetailsResponse
from services.geolocation.coord_to_address import coord_to_address

property_routes = APIRouter(prefix="/property")

@property_routes.get("/search_by_property_address/address={address}", dependencies=[Depends(validate_api_key)], response_model=PropertyDetailsResponse)
def search_by_address(address: str, db: DatabaseConnector = Depends(get_db)) -> PropertyDetailsResponse:
    """Searches for a property by its address.

    Args:
        address (str): The address of the property to search for.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        PropertyDetailsResponse: A response object containing the property information.
    """
    return search_by_property_address(address, db)

@property_routes.get("/search_by_property_bbl/bbl={bbl}", dependencies=[Depends(validate_api_key)], response_model=PropertyDetailsResponse)
def search_by_bbl(bbl:str, db: DatabaseConnector = Depends(get_db)) -> PropertyDetailsResponse:
    """Searches for a property by its BBL (Borough, Block, Lot).

    Args:
        bbl (str): The BBL of the property to search for.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        PropertyDetailsResponse: A response object containing the property information.
    """
    return search_by_property_bbl(bbl, db)

@property_routes.get("/search_by_fuzzy_coords/lat={lat}/long={long}", dependencies=[Depends(validate_api_key)], response_model=PropertyDetailsResponse)
def search_by_fuzz_coords(lat: str, long: str, db: DatabaseConnector = Depends(get_db)) -> Union[PropertyDetailsResponse, Dict[str, Union[str, int]]]:
    """Searches for a property by its fuzzy coordinates.

    Args:
        lat (str): The latitude of the property.
        long (str): The longitude of the property.
        db (DatabaseConnector, optional): The database connector. Defaults to Depends(get_db).

    Returns:
        Union[PropertyDetailsResponse, Dict]: A response object containing the property information, or an error message dictionary.
    """
    try:
        address = coord_to_address(float(lat), float(long))['address']
        return search_by_property_address(address, db)
    except KeyError:
        return {"message":"Unable to convert coords", "status_code":500}
    except TypeError:
        return {"message":"Address not in New York", "status_code":500}
    except Exception as e:
        return {"message":"Unknown error: " + str(e), "status_code":500}
