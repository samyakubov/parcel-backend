import requests

from pydantic_models import CensusGeoCodeResponse


def geocode_address(address: str) -> CensusGeoCodeResponse:
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

    # Safely get congressional district
    congressional_districts = match["geographies"].get("119th Congressional Districts", [])
    congressional_district = congressional_districts[0]["GEOID"] if congressional_districts else None

    return {
        "lat": match["coordinates"]["y"],
        "lon": match["coordinates"]["x"],
        "matchedAddress": match["matchedAddress"],
        "tract": match["geographies"]["Census Tracts"][0]["GEOID"],
        "blockGroup": match["geographies"]["2020 Census Blocks"][0]["BLKGRP"],
        "block": match["geographies"]["2020 Census Blocks"][0]["GEOID"],
        "county": match["geographies"]["Counties"][0]["GEOID"],
        "state": match["geographies"]["States"][0]["GEOID"],
        "countyName": match["geographies"]["Counties"][0]["BASENAME"],
        "stateName": match["geographies"]["States"][0]["BASENAME"],
        "city": match["addressComponents"]["city"],
        "zip": match["addressComponents"]["zip"],
        "congressionalDistrict": congressional_district
    }