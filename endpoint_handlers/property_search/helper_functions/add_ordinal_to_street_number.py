import re
from logger_config import logger

def _ordinal(n):
    try:
        n = int(n)
        if 10 <= n % 100 <= 20:
            suffix = 'th'
        else:
            suffix = {1:'st', 2:'nd', 3:'rd'}.get(n % 10, 'th')
        return f"{n}{suffix}"
    except (ValueError, TypeError):
        logger.warning(f"Could not convert '{n}' to an integer for ordinal conversion.")
        return n


def add_ordinal_to_street_number(address):
    if not isinstance(address, str):
        logger.warning(f"add_ordinal_to_street_number received a non-string value: {address}")
        return address
        
    match = re.match(r'^(.*?\s)?(\d+)(\s.*)', address)
    if match:
        prefix = match.group(1) or ''
        number = match.group(2)
        rest = match.group(3) or ''
        return f"{prefix}{_ordinal(number)}{rest}"
    
    logger.info(f"Regex for adding ordinal did not match for address: '{address}'. Returning original address.")
    return address