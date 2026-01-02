from geopy.exc import GeocoderServiceError, GeocoderTimedOut

from exceptions.geolocation_exceptions import (
    AddressNotInNewYorkError,
    GeolocationError,
)
from logger_config import logger
from services.geolocation.address_to_coord import NYC_BOUNDS
from services.geolocation.geolocation_helper import get_geolocator



def is_in_nyc_bounds(latitude: float, longitude: float) -> bool:
    """
    Check if coordinates are within NYC geographic bounds.

    Args:
        latitude: Latitude coordinate
        longitude: Longitude coordinate

    Returns:
        bool: True if coordinates are in NYC bounds, False otherwise
    """
    return (NYC_BOUNDS['min_lat'] <= latitude <= NYC_BOUNDS['max_lat'] and
            NYC_BOUNDS['min_lon'] <= longitude <= NYC_BOUNDS['max_lon'])


def coord_to_address(latitude: float, longitude: float) -> dict[str, str] | None:
    """
    Convert geographic coordinates into a formatted street address.
    Only accepts coordinates within NYC bounds.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        dict | None: A dictionary containing the formatted address,
            or None if lookup fails.

    Raises:
        GeolocationError: If the geocoding service fails.
        AddressNotInNewYorkError: If the coordinates are not in New York.
    """
    if latitude is None or longitude is None:
        logger.warning("Latitude and/or longitude were not provided for reverse geocoding.")
        return None

    if not is_in_nyc_bounds(latitude, longitude):
        error_msg = f"Coordinates ({latitude}, {longitude}) are outside NYC bounds"
        logger.warning(error_msg)
        raise AddressNotInNewYorkError(error_msg)

    try:
        geolocator = get_geolocator()

        location = geolocator.reverse((latitude, longitude))
        if not location:
            logger.warning(f"Could not find address for coordinates: ({latitude}, {longitude})")
            return None

        formatted_address = location.address

        address_lower = formatted_address.lower()
        is_in_ny = "new york" in address_lower or ", ny" in address_lower

        if not is_in_ny:
            logger.warning(
                f"Address found for coordinates ({latitude}, {longitude}) is not in New York: '{formatted_address}'"
            )
            raise AddressNotInNewYorkError(f"Address is not in New York: {formatted_address}")

        logger.info(
            f"Successfully reverse geocoded coordinates ({latitude}, {longitude}) to address: '{formatted_address}'"
        )

        return {"address": formatted_address.split(", ")[0]}

    except AddressNotInNewYorkError:
        raise
    except GeocoderTimedOut as e:
        logger.error(
            f"The geocoding service timed out while processing coordinates: ({latitude}, {longitude}).",
            exc_info=True
        )
        raise GeolocationError(f"Geocoding service timed out for coordinates: ({latitude}, {longitude})") from e
    except GeocoderServiceError as e:
        logger.error(
            f"A geocoding service error occurred for coordinates ({latitude}, {longitude}): {e}",
            exc_info=True
        )
        raise GeolocationError(f"Geocoding service error: {e}") from e
    except Exception as e:
        logger.error(
            f"Unexpected error during reverse geocoding for coordinates ({latitude}, {longitude}): {e}",
            exc_info=True
        )
        raise GeolocationError(f"Unexpected geocoding error: {e}") from e