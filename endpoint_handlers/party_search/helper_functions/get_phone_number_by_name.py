from database_connector import db

def get_phone_number_by_name(party_name:str):
    try:
        phone_numbers = db.execute_df("SELECT ownersphone AS owners_phone FROM dobjobs WHERE ownername LIKE ?", [party_name])


    except Exception as e:
        return {"message": "An unexpected error has occurred", "status_code": 500}
