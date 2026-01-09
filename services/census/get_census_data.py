import os
import requests
from pydantic_models import CensusDemographicData


def get_census_data_handler(tract_id: str) -> CensusDemographicData:
    # Extract state, county, and tract from the GEOID
    # Format: SSCCCTTTTTT (2 state + 3 county + 6 tract)
    state = tract_id[0:2]
    county = tract_id[2:5]
    tract = tract_id[5:]

    variables = [
        "B01003_001E",  # Total Population
        "B19013_001E",  # Median Household Income
        "B25077_001E",  # Median Home Value
        "B25064_001E",  # Median Gross Rent
        "B01002_001E"   # Median Age
    ]

    url = "https://api.census.gov/data/2022/acs/acs5"

    response = requests.get(
        url,
        headers={
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        params={
            "get": f"NAME,{','.join(variables)}",
            "for": f"tract:{tract}",
            "in": f"state:{state}+county:{county}",
            "key": os.environ.get("CENSUS_API_KEY")
        }
    )

    data = response.json()

    return {
        "tractName": data[1][0],
        "population": int(data[1][1]) if data[1][1] and data[1][1] != "-666666666" else None,
        "medianIncome": int(data[1][2]) if data[1][2] and data[1][2] != "-666666666" else None,
        "medianHomeValue": int(data[1][3]) if data[1][3] and data[1][3] != "-666666666" else None,
        "medianRent": int(data[1][4]) if data[1][4] and data[1][4] != "-666666666" else None,
        "medianAge": float(data[1][5]) if data[1][5] and data[1][5] != "-666666666" else None
    }