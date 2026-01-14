import requests

from schemas import CensusGeoCodeResponse


def geocode_address(address: str) -> CensusGeoCodeResponse:
    """
    Geocodes an address to a census tract.

    Args:
        address: The address to geocode.

    Returns:
        A dictionary containing the census tract ID.
    """
    url = "https://geocoding.geo.census.gov/geocoder/geographies/onelineaddress"

    response = requests.get(
        url,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        params={
            "address": address,
            "benchmark": "Public_AR_Current",
            "vintage": "Current_Current",
            "format": "json"
        }
    )

    data = response.json()

    if not data.get("result", {}).get("addressMatches") or len(data["result"]["addressMatches"]) == 0:
        raise Exception("Address not found in Census geocoder")

    match = data["result"]["addressMatches"][0]


    return {"tract": match["geographies"]["Census Tracts"][0]["GEOID"]}