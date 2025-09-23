import pandas as pd
from database_connector import db
from endpoint_handlers.property_search.helper_functions.standardize_address_for_database import standardize_address
from logger_config import logger


def get_complaint_data(address: str):
    parts = standardize_address(address).strip().split(' ', 1)
    if len(parts) != 2:
        return []

    house_number, street = parts
    street = street.strip().upper()
    try:
        df = db.execute_df("""SELECT 
                                complaintnumber as complaint_number,
                                dateentered as date_entered,
                                specialdistrict as special_district,
                                complaintcategory as complaint_category,
                                dispositiondate as disposition_date,
                                dispositioncode as disposition_code,
                                inspectiondate as inspection_date,
                                dobrundate as dobrun_date,
                                bin as bin,
                              FROM dob_complaints 
                              WHERE 
                                  housenumber = ? 
                                AND housestreet LIKE ? ORDER BY dateentered DESC""",
                           [str(house_number), f"{street}%"])
        if df.empty:
            return []

        date_columns = ['date_entered', 'disposition_date', 'inspection_date', 'dobrun_date']
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col]).dt.strftime('%Y-%m-%d')

        df = df.sort_values('date_entered', ascending=False)

        return df.to_dict(orient="records")
    except Exception as e:
        logger.error(f"Error retrieving complaints for address {address}: {str(e)}")
        return []