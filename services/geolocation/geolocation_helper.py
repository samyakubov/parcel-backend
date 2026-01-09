import os

from geopy.geocoders import MapBox


def get_geolocator() -> MapBox:
    """Creates a configured MapBox geolocator.

    Returns:
        MapBox: A configured geolocator instance.
    Raises:
        ValueError: If MAPBOX_API_KEY is not set in environment variables.
    """
    api_key = os.getenv("MAPBOX_API_KEY")
    if not api_key:
        raise ValueError("MAPBOX_API_KEY environment variable is not set")

    return MapBox(api_key=api_key, user_agent="parcel", scheme="https", timeout=10)
