import ssl
import certifi
from geopy.geocoders import Nominatim


def get_geolocator() -> Nominatim:
    """Creates a configured Nominatim geolocator with SSL context.
    
    Returns:
        Nominatim: A configured geolocator instance.
    """
    ctx = ssl.create_default_context(cafile=certifi.where())
    return Nominatim(user_agent="parcel", scheme="https", timeout=10, ssl_context=ctx)
