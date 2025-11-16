class GeolocationError(Exception):
    """Exception raised when geolocation services fail."""

    def __init__(self, message: str = "Geolocation service failed"):
        self.message = message
        super().__init__(self.message)


class AddressNotInNewYorkError(Exception):
    """Exception raised when an address is not in New York."""

    def __init__(self, message: str = "Address is not in New York"):
        self.message = message
        super().__init__(self.message)
