import pandas as pd


def match_phone_numbers_to_owner(phone_numbers: pd.DataFrame, owners_list: list) -> list[str]:
    """Matches phone numbers to a list of owner names.

    Args:
        phone_numbers (pd.DataFrame): A DataFrame containing owner names
            and phone numbers. Must have the columns 'owner_full_name'
            and 'owners_phone'.
        owners_list (list): A list of owner names to match against.

    Returns:
        List[str]: A list of strings, where each string is the owner's
            name and their phone number in the format
            "owner_name (phone_number)". If no phone number is found,
            it will be "owner_name (No Phone Number)".
    """
    owners_df = pd.DataFrame({"owner_full_name": owners_list})

    merged_df = owners_df.merge(phone_numbers[["owner_full_name", "owners_phone"]], on="owner_full_name", how="left")

    merged_df["owners_phone"] = merged_df["owners_phone"].fillna("No Phone Number")

    result = merged_df.apply(lambda row: f"{row['owner_full_name']} ({row['owners_phone']})", axis=1)

    return result.tolist()
