import pandas as pd


def match_phone_numbers_to_owner(phone_numbers: pd.DataFrame | list, owners_list: list) -> list[str]:
    """Matches phone numbers to a list of owner names.

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
    owners_df = pd.DataFrame({"owner_full_name": owners_list})

    # Handle case when phone_numbers is an empty list
    if isinstance(phone_numbers, list) or phone_numbers.empty:
        owners_df["owners_phone"] = "No Phone Number"
    else:
        merged_df = owners_df.merge(phone_numbers[["owner_full_name", "owners_phone"]], on="owner_full_name", how="left")
        owners_df = merged_df
        owners_df["owners_phone"] = owners_df["owners_phone"].fillna("No Phone Number")

    result = owners_df.apply(lambda row: f"{row['owner_full_name']} ({row['owners_phone']})", axis=1)

    return result.tolist()
