import pandas as pd

def match_phone_numbers_to_owner(phone_numbers: pd.DataFrame, owners_list: list):
    owners_df = pd.DataFrame({'owner_full_name': owners_list})

    merged_df = owners_df.merge(phone_numbers[['owner_full_name', 'owners_phone']],
                                on='owner_full_name', how='left')

    merged_df['owners_phone'] = merged_df['owners_phone'].fillna('No Phone Number')

    result = merged_df.apply(lambda row: f"{row['owner_full_name']} ({row['owners_phone']})", axis=1)

    return result.tolist()
