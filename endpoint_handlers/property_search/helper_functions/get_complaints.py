import pandas as pd
from database_connector import db
from endpoint_handlers.property_search.helper_functions.standardize_address_for_database import standardize_address


def get_complaint_data(address: str):

    parts = standardize_address(address).strip().split(' ', 1)
    if len(parts) != 2:
        return []

    house_number, street = parts

    street = street.strip().upper()
    try:
        df = db.execute_df(" SELECT * FROM DOBComplaint WHERE housenumber LIKE ? AND housestreet LIKE ? ORDER BY dateentered DESC", [f"{house_number}%", f"{street}%"])

        if df.empty:
            return []

        date_columns = ['dateentered', 'dispositiondate', 'inspectiondate', 'dobrundate']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d')

        df = df.sort_values('dateentered', ascending=False)

        df = df.rename(columns={
            'complaintnumber': 'complaint_number',
            'dateentered': 'date_entered',
            'housenumber': 'house_number',
            'housestreet': 'house_street',
            'communityboard': 'community_board',
            'specialdistrict': 'special_district',
            'complaintcategory': 'complaint_category',
            'dispositiondate': 'disposition_date',
            'dispositioncode': 'disposition_code',
            'inspectiondate': 'inspection_date',
            'dobrundate': 'dobrun_date'
        })

        return df.fillna("").to_dict(orient="records")

    except Exception as e:
        print(f"Error retrieving complaints for address {address}: {str(e)}")
        return []