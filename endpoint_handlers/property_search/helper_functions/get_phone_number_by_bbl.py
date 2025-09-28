from database_connector import db
from logger_config import logger


def get_phone_number_by_bbl(bbl:str):
    try:
        phone_numbers = db.execute_df("SELECT distinct ownersphone as owners_phone, ownersfirstname as owners_first_name, ownerslastname as owners_last_name FROM dobjobs WHERE bbl = ?", [bbl])
        phone_numbers["owner_full_name"] = phone_numbers["owners_last_name"].fillna('') + ", " + phone_numbers["owners_first_name"].fillna('')
        return phone_numbers
    except Exception as e:
        logger.error(e)
        return []
