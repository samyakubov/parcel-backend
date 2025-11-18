class GeolocationError(Exception):
    """Exception raised when geolocation services fail."""
    pass


class AddressNotInNewYorkError(Exception):
    """Exception raised when an address is not in New York."""
    pass
