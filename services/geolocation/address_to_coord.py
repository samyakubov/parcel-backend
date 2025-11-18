from geopy.exc import GeocoderServiceError, GeocoderTimedOut

from exceptions.geolocation_exceptions import GeolocationError
from logger_config import logger
from pydantic_models import Coordinates
from services.geolocation.geolocation_helper import get_geolocator


def address_to_coord(address: str) -> Coordinates | None:
    """
    Convert a street address into geographic coordinates.

    Args:
        address (str): The address to lookup.

    Returns:
        Coordinates | None: A Coordinates object with latitude and longitude,
            or None if lookup fails.

    Raises:
        GeolocationError: If the geocoding service fails.
    """
    if not address:
        logger.warning("No address was provided for geocoding.")
        return None
    try:
        geolocator = get_geolocator()

        location = geolocator.geocode(address)

        if location:
            logger.info(
                f"Successfully geocoded address '{address}' to coordinates: ({location.latitude}, {location.longitude})\n"
            )
            return Coordinates(latitude=location.latitude, longitude=location.longitude)
        else:
            logger.warning(f"Could not find location for address: '{address}'")
            return None

    except GeocoderTimedOut as e:
        logger.error(f"The geocoding service timed out while processing address: '{address}'.", exc_info=True)
        raise GeolocationError(f"Geocoding service timed out for address: {address}") from e
    except GeocoderServiceError as e:
        logger.error(f"A geocoding service error occurred for address '{address}': {e}", exc_info=True)
        raise GeolocationError(f"Geocoding service error: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during geocoding for address '{address}': {e}", exc_info=True)
        raise GeolocationError(f"Unexpected geocoding error: {e}") from e
