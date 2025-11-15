from typing import Dict
from fastapi import APIRouter, Depends
from endpoint_handlers.api_keys.validate_api_key import validate_api_key
from endpoint_handlers.property_search.search_by_property_address import search_by_property_address
from endpoint_handlers.property_search.search_by_property_bbl import search_by_property_bbl
from services.geolocation.coord_to_address import coord_to_address

property_routes = APIRouter(prefix="/property")

@property_routes.get("/search_by_property_address/address={address}", dependencies=[Depends(validate_api_key)], response_model=Dict)
def search_by_address(address):
    return search_by_property_address(address)

@property_routes.get("/search_by_property_bbl/bbl={bbl}", response_model=Dict)
def search_by_bbl(bbl:str):
    return search_by_property_bbl(bbl)

@property_routes.get("/search_by_fuzzy_coords/lat={lat}/long={long}", response_model=Dict)
def search_by_fuzz_coords(lat,long):
    try:
        address = coord_to_address(lat, long)['address']
        return search_by_property_address(address)
    except KeyError:
        return {"message":"Unable to convert coords", "status_code":500}
    except TypeError:
        return {"message":"Address not in New York", "status_code":500}
    except Exception as e:
        return {"message":"Unknown error: " + str(e), "status_code":500}
