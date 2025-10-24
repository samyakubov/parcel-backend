class BBLNotFoundException(Exception):
    """Raised when no records are found for a given BBL"""
    def __init__(self, bbl: str):
        self.bbl = bbl
        super().__init__(f"No records found for BBL: {bbl}")


class InvalidBBLException(Exception):
    """Raised when BBL is empty or invalid"""
    def __init__(self, message: str = "Invalid BBL provided"):
        self.message = message
        super().__init__(self.message)


class InvalidAddressException(Exception):
    def __init__(self, message: str = "Invalid address provided"):
        self.message = message
        super().__init__(self.message)

    def __str__(self):
        return self.message


class AddressNotFoundException(Exception):
    def __init__(self, address: str):
        self.address = address
        self.message = f"No records found for address: {address}"
        super().__init__(self.message)

    def __str__(self):
        return self.message