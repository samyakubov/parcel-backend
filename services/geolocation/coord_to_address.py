from geopy.exc import GeocoderServiceError, GeocoderTimedOut

from exceptions.geolocation_exceptions import (
    AddressNotInNewYorkError,
    GeolocationError,
)
from logger_config import logger
from services.geolocation.geolocation_helper import get_geolocator


def coord_to_address(latitude: float, longitude: float) -> dict[str, str] | None:
    """
    Convert geographic coordinates into a formatted street address.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        dict | None: A dictionary containing the formatted address,
            or None if lookup fails.

    Raises:
        GeolocationError: If the geocoding service fails.
        AddressNotInNewYorkError: If the address is not in New York.
    """
    if latitude is None or longitude is None:
        logger.warning("Latitude and/or longitude were not provided for reverse geocoding.")
        return None
    try:
        geolocator = get_geolocator()

        location = geolocator.reverse((latitude, longitude))
        if not location:
            logger.warning(f"Could not find address for coordinates: ({latitude}, {longitude})")
            return None

        address_lower = location.address.lower()
        is_in_ny = "new york" in address_lower or ", ny" in address_lower
        
        if not is_in_ny:
            logger.warning(
                f"Address found for coordinates ({latitude}, {longitude}) is not in New York: '{location.address}'"
            )
            raise AddressNotInNewYorkError(f"Address is not in New York: {location.address}")


        
        raw = location.raw.get("address", {})
        house_number = raw.get("house_number", "")
        road = raw.get("road", "")
        
        if house_number and road:
            formatted_address = f"{house_number} {road}"
        elif road:
            formatted_address = road
        else:
            parts = location.address.split(",")
            formatted_address = parts[0].strip() if parts else location.address

        logger.info(
            f"Successfully reverse geocoded coordinates ({latitude}, {longitude}) to address: '{formatted_address}'"
        )
        return {"address": formatted_address}

    except AddressNotInNewYorkError:
        raise
    except GeocoderTimedOut as e:
        logger.error(
            f"The geocoding service timed out while processing coordinates: ({latitude}, {longitude}).", exc_info=True
        )
        raise GeolocationError(f"Geocoding service timed out for coordinates: ({latitude}, {longitude})") from e
    except GeocoderServiceError as e:
        logger.error(
            f"A geocoding service error occurred for coordinates ({latitude}, {longitude}): {e}", exc_info=True
        )
        raise GeolocationError(f"Geocoding service error: {e}") from e
    except Exception as e:
        logger.error(
            f"Unexpected error during reverse geocoding for coordinates ({latitude}, {longitude}): {e}", exc_info=True
        )
        raise GeolocationError(f"Unexpected geocoding error: {e}") from e
