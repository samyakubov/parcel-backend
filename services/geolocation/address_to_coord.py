from geopy.exc import GeocoderServiceError, GeocoderTimedOut

from exceptions.geolocation_exceptions import GeolocationError
from logger_config import logger
from pydantic_models import Coordinates
from services.geolocation.geolocation_helper import get_geolocator

NYC_BOUNDS = {
    'min_lat': 40.4774,   # Southern tip of Staten Island
    'max_lat': 40.9176,   # Northern Bronx
    'min_lon': -74.2591,  # Western Staten Island
    'max_lon': -73.7004   # Eastern Queens
}


def address_to_coord(address: str) -> Coordinates | None:
    """
    Convert a street address into geographic coordinates within NYC.

    Args:
        address (str): The address to lookup.

    Returns:
        Coordinates | None: A Coordinates object with latitude and longitude,
            or None if lookup fails or address is outside NYC.

    Raises:
        GeolocationError: If the geocoding service fails.
    """
    if not address:
        logger.warning("No address was provided for geocoding.")
        return None

    try:
        geolocator = get_geolocator()

        search_address = f"{address}, New York, NY, USA"

        location = geolocator.geocode(search_address)

        if location:
            lat = location.latitude
            lon = location.longitude

            if (NYC_BOUNDS['min_lat'] <= lat <= NYC_BOUNDS['max_lat'] and
                    NYC_BOUNDS['min_lon'] <= lon <= NYC_BOUNDS['max_lon']):

                logger.info(
                    f"Successfully geocoded address '{address}' to NYC coordinates: ({lat}, {lon})\n"
                )
                return Coordinates(latitude=lat, longitude=lon)
            else:
                logger.warning(
                    f"Address '{address}' geocoded to coordinates ({lat}, {lon}) which are outside NYC bounds. Rejecting."
                )
                return None
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