class BBLNotFoundError(Exception):
    """Exception raised when a BBL is not found."""

    def __init__(self, bbl: str):
        self.bbl = bbl
        super().__init__(f"No records found for BBL: {bbl}")


class InvalidBBLError(Exception):
    """Exception raised when a BBL is invalid."""

    def __init__(self, message: str = "Invalid BBL provided"):
        self.message = message
        super().__init__(self.message)


class InvalidAddressError(Exception):
    """Exception raised when an address is invalid."""

    def __init__(self, message: str = "Invalid address provided"):
        self.message = message
        super().__init__(self.message)


class AddressNotFoundError(Exception):
    """Exception raised when an address is not found."""

    def __init__(self, address: str):
        self.address = address
        super().__init__(f"No records found for address: {self.address}")
