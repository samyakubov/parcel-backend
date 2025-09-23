from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import ssl
import certifi
from logger_config import logger

def coord_to_address(latitude: float, longitude: float):
    try:
        if latitude is None or longitude is None:
            logger.error("Latitude and longitude must be provided")
            return

        ctx = ssl.create_default_context(cafile=certifi.where())

        geolocator = Nominatim(
            user_agent="parcel",
            scheme='https',
            timeout=10,
            ssl_context=ctx
        )

        location = geolocator.reverse((latitude, longitude))
        formatted_address = location.address
        parts = location.address.split(',')
        if "new york" not in parts[5].strip().lower():
            return

        if len(parts) >= 2:
            formatted_address = f"{parts[0].strip()} {parts[1].strip()}"

        if location:
            return {"address": formatted_address}
        else:
            logger.error("Location not found")

    except GeocoderTimedOut:
        logger.error("The geocoding service timed out. Please try again later.")
    except GeocoderServiceError as g:
        logger.error(f"Geocoding service error: {g}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
