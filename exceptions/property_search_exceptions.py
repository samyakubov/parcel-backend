class BBLNotFoundError(Exception):
    """Exception raised when a BBL is not found."""
    pass


class InvalidBBLError(Exception):
    """Exception raised when a BBL is invalid."""
    pass


class InvalidAddressError(Exception):
    """Exception raised when an address is invalid."""
    pass


class AddressNotFoundError(Exception):
    """Exception raised when an address is not found."""
    pass
