import os
import requests
from schemas import CensusDemographicData, RaceDemographic


def get_census_data_handler(tract_id: str) -> CensusDemographicData:
    """
    Gets census data for a given census tract.

    Args:
        tract_id: The census tract ID.

    Returns:
        A dictionary containing census data.
    """
    state = tract_id[0:2]
    county = tract_id[2:5]
    tract = tract_id[5:]

    variables = [
        "B01003_001E",  # Total Population
        "B19013_001E",  # Median Household Income
        "B25077_001E",  # Median Home Value
        "B25064_001E",  # Median Gross Rent
        "B01002_001E",  # Median Age
        "B02001_002E",  # White Alone
        "B02001_003E",  # Black or African American Alone
        "B02001_004E",  # American Indian and Alaska Native Alone
        "B02001_005E",  # Asian Alone
        "B03003_003E",  # Hispanic or Latino
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

    white = int(data[1][6]) if data[1][6] and data[1][6] != "-666666666" else 0
    black = int(data[1][7]) if data[1][7] and data[1][7] != "-666666666" else 0
    native_american = int(data[1][8]) if data[1][8] and data[1][8] != "-666666666" else 0
    asian = int(data[1][9]) if data[1][9] and data[1][9] != "-666666666" else 0
    hispanic = int(data[1][10]) if data[1][10] and data[1][10] != "-666666666" else 0

    total_pop = int(data[1][1]) if data[1][1] and data[1][1] != "-666666666" else 0
    other = max(0, total_pop - (white + black + native_american + asian + hispanic))

    race_demographics_raw = [
        {"label": "White", "value": white},
        {"label": "Black or African American", "value": black},
        {"label": "Asian", "value": asian},
        {"label": "Hispanic or Latino", "value": hispanic},
        {"label": "Native American", "value": native_american},
        {"label": "Other", "value": other}
    ]

    race_demographics = [
        RaceDemographic(**item)
        for item in race_demographics_raw
        if item["value"] > 0
    ]

    return CensusDemographicData(
        population=total_pop if total_pop > 0 else None,
        medianIncome=int(data[1][2]) if data[1][2] and data[1][2] != "-666666666" else None,
        medianHomeValue=int(data[1][3]) if data[1][3] and data[1][3] != "-666666666" else None,
        medianRent=int(data[1][4]) if data[1][4] and data[1][4] != "-666666666" else None,
        medianAge=float(data[1][5]) if data[1][5] and data[1][5] != "-666666666" else None,
        raceDemographics=race_demographics
    )