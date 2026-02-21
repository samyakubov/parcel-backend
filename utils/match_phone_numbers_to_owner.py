
import pandas as pd


def normalize_name(name: str) -> str:
    """Normalizes a name for matching."""
    if not name:
        return ""
    return str(name).strip().upper()

def match_phone_numbers_to_owner(phone_numbers: pd.DataFrame | list, owners_list: list) -> list[str]:
    """Matches phone numbers to a list of owner names with fuzzy handling for name formats.

    Args:
        phone_numbers (pd.DataFrame | list): A DataFrame containing owner names
            and phone numbers. Must have the columns 'owner_full_name'
            and 'owners_phone'. Can also be an empty list if no phone numbers found.
        owners_list (list): A list of owner names to match against.

    Returns:
        List[str]: A list of strings, where each string is the owner's
            name and their phone number in the format
            "owner_name (phone_number)". If no phone number is found,
            it will be "owner_name (No Phone Number)".
    """
    if isinstance(phone_numbers, list) or phone_numbers.empty:
        return [f"{owner} (No Phone Number)" for owner in owners_list]



    phone_map = {}

    for _, row in phone_numbers.iterrows():
        name = normalize_name(row["owner_full_name"])
        phone = row["owners_phone"]
        if name:
            phone_map[name] = phone


            cleaned = name.replace(",", "").replace(".", "")
            if cleaned != name:
                phone_map[cleaned] = phone

    result = []
    for owner in owners_list:
        normalized_owner = normalize_name(owner)
        phone_number = "No Phone Number"


        if normalized_owner in phone_map:
            phone_number = phone_map[normalized_owner]


        elif "," in normalized_owner:
            parts = normalized_owner.split(",", 1)
            if len(parts) == 2:

                first_last = f"{parts[1].strip()} {parts[0].strip()}"
                if first_last in phone_map:
                    phone_number = phone_map[first_last]


                cleaned_owner = normalized_owner.replace(",", "").replace(".", "")
                if cleaned_owner in phone_map:
                    phone_number = phone_map[cleaned_owner]

        result.append(f"{owner} ({phone_number})")

    return result
