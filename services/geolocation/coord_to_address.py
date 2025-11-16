import ssl

import certifi
from geopy.exc import GeocoderServiceError, GeocoderTimedOut
from geopy.geocoders import Nominatim

from exceptions.geolocation_exceptions import (
    AddressNotInNewYorkError,
    GeolocationError,
)
from logger_config import logger


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
        ctx = ssl.create_default_context(cafile=certifi.where())

        geolocator = Nominatim(user_agent="parcel", scheme="https", timeout=10, ssl_context=ctx)

        location = geolocator.reverse((latitude, longitude))
        if not location:
            logger.warning(f"Could not find address for coordinates: ({latitude}, {longitude})")
            return None

        formatted_address = location.address
        parts = location.address.split(",")
        if len(parts) < 6 or "new york" not in parts[5].strip().lower():
            logger.warning(
                f"Address found for coordinates ({latitude}, {longitude}) is not in New York: '{location.address}'"
            )
            raise AddressNotInNewYorkError(f"Address is not in New York: {location.address}")

        if len(parts) >= 2:
            formatted_address = f"{parts[0].strip()} {parts[1].strip()}"

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
