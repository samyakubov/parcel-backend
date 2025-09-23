import re


def _ordinal(n):
    n = int(n)
    if 10 <= n % 100 <= 20:
        suffix = 'th'
    else:
        suffix = {1:'st', 2:'nd', 3:'rd'}.get(n % 10, 'th')
    return f"{n}{suffix}"

def add_ordinal_to_street_number(address):
    match = re.match(r'^(.*?\s)?(\d+)(\s.*)', address)
    if match:
        prefix = match.group(1) or ''
        number = match.group(2)
        rest = match.group(3) or ''
        return f"{prefix}{_ordinal(number)}{rest}"
    return address
