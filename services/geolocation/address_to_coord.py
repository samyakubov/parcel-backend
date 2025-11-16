from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import ssl
import certifi
from logger_config import logger
from pydantic_models import Coordinates
from typing import Optional
from exceptions.geolocation_exceptions import GeolocationException


def address_to_coord(address: str) -> Optional[Coordinates]:
    """
    Convert a street address into geographic coordinates.

    Args:
        address (str): The address to lookup.

    Returns:
        Coordinates | None: A Coordinates object with latitude and longitude, or None if lookup fails.
        
    Raises:
        GeolocationException: If the geocoding service fails.
    """
    if not address:
        logger.warning("No address was provided for geocoding.")
        return None
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())

        geolocator = Nominatim(
            user_agent="parcel",
            scheme='https',
            timeout=10,
            ssl_context=ctx
        )

        location = geolocator.geocode(address)

        if location:
            logger.info(f"Successfully geocoded address '{address}' to coordinates: ({location.latitude}, {location.longitude})")
            return Coordinates(latitude=location.latitude, longitude=location.longitude)
        else:
            logger.warning(f"Could not find location for address: '{address}'")
            return None

    except GeocoderTimedOut:
        logger.error(f"The geocoding service timed out while processing address: '{address}'.", exc_info=True)
        raise GeolocationException(f"Geocoding service timed out for address: {address}")
    except GeocoderServiceError as e:
        logger.error(f"A geocoding service error occurred for address '{address}': {e}", exc_info=True)
        raise GeolocationException(f"Geocoding service error: {e}")
    except Exception as e:
        logger.error(f"Unexpected error during geocoding for address '{address}': {e}", exc_info=True)
        raise GeolocationException(f"Unexpected geocoding error: {e}")