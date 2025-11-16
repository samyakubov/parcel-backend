import re

from logger_config import logger

ABBREVIATIONS = {
    r"\bave\b": "avenue",
    r"\bavn\b": "avenue",
    r"\bavnue\b": "avenue",
    r"\baven\b": "avenue",
    r"\bst\b": "street",
    r"\bstr\b": "street",
    r"\bstrt\b": "street",
    r"\bblvd\b": "boulevard",
    r"\bblv\b": "boulevard",
    r"\bboul\b": "boulevard",
    r"\bdr\b": "drive",
    r"\bdrv\b": "drive",
    r"\bct\b": "court",
    r"\bcour\b": "court",
    r"\brd\b": "road",
    r"\brod\b": "road",
    r"\bapt\b": "apartment",
    r"\bapmt\b": "apartment",
    r"\baptmt\b": "apartment",
    r"\bsuite\b": "suite",
    r"\bste\b": "suite",
    r"\bln\b": "lane",
    r"\blane\b": "lane",
    r"\bpl\b": "place",
    r"\bplc\b": "place",
}

ABBREVIATIONS_COMPILED = {re.compile(pattern): replacement for pattern, replacement in ABBREVIATIONS.items()}


def standardize_address(address: str) -> str:
    """Standardizes an address string.

    This function takes an address string and performs the following standardizations:
    - Converts the address to lowercase.
    - Replaces common abbreviations with their full words (e.g., "st" to "street").
    - Removes ordinal suffixes from numbers (e.g., "1st" to "1").
    - Removes extra whitespace.
    - Converts the entire address to uppercase.

    Args:
        address (str): The address string to standardize.

    Returns:
        str: The standardized address string.

    Raises:
        ValueError: If the address is not a string or cannot be converted to a string.
    """
    if not isinstance(address, str):
        logger.warning(f"standardize_address received a non-string value: {address}")
        try:
            address = str(address)
        except Exception as e:
            logger.error(f"Could not convert input to string in standardize_address: {e}", exc_info=True)
            raise ValueError("Address must be a string or convertible to a string.") from e

    address = address.lower()

    for pattern, replacement in ABBREVIATIONS_COMPILED.items():
        address = pattern.sub(replacement, address)

    address = re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", address)

    address = re.sub(r"\s+", " ", address).strip()

    address = " ".join(word.upper() for word in address.split())

    return address
