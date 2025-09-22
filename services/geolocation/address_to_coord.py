from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut, GeocoderServiceError
import ssl
import certifi
from logger_config import logger


def address_to_coord(address: str):
    if not address:
        logger.error("No address was provided")
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
            return {
                "latitude": location.latitude,
                "longitude": location.longitude
            }
        else:
            logger.error("Address not found")

    except GeocoderTimedOut:
        logger.error("The geocoding service timed out. Please try again later.")
    except GeocoderServiceError as g:
        logger.error(f"Geocoding service error: {g}")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
