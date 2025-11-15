from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import ssl
import certifi
from logger_config import logger

def coord_to_address(latitude: float, longitude: float):
    if latitude is None or longitude is None:
        logger.error("Latitude and/or longitude were not provided for reverse geocoding.")
        return None
    try:
        ctx = ssl.create_default_context(cafile=certifi.where())

        geolocator = Nominatim(
            user_agent="parcel",
            scheme='https',
            timeout=10,
            ssl_context=ctx
        )

        location = geolocator.reverse((latitude, longitude))
        if not location:
            logger.warning(f"Could not find address for coordinates: ({latitude}, {longitude})")
            return None

        formatted_address = location.address
        parts = location.address.split(',')
        if "new york" not in parts[5].strip().lower():
            logger.warning(f"Address found for coordinates ({latitude}, {longitude}) is not in New York: '{location.address}'")
            return None

        if len(parts) >= 2:
            formatted_address = f"{parts[0].strip()} {parts[1].strip()}"
        
        logger.info(f"Successfully reverse geocoded coordinates ({latitude}, {longitude}) to address: '{formatted_address}'")
        return {"address": formatted_address}

    except GeocoderTimedOut:
        logger.error(f"The geocoding service timed out while processing coordinates: ({latitude}, {longitude}).", exc_info=True)
        return None
    except GeocoderServiceError as e:
        logger.error(f"A geocoding service error occurred for coordinates ({latitude}, {longitude}): {e}", exc_info=True)
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred during reverse geocoding for coordinates ({latitude}, {longitude}): {e}", exc_info=True)
        return None